"""
FastAPI Server for Knowledge Brain (Task 1).
Provides query endpoint, ingestion management, escalation workflow, and health checks.
"""

import json
import logging
import os
import threading
from typing import List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .schemas import (
    QueryRequest, QueryResponse,
    IngestionRequest, IngestionResponse,
    EscalationCreateRequest, EscalationResolveRequest, EscalationItem,
    HealthResponse
)
from ..crawler.polite_crawler import PoliteCrawler
from ..rag.chunker import DocumentChunker
from ..rag.embeddings import get_embedding_generator
from ..rag.vector_store import VectorStore
from ..rag.hybrid_retriever import HybridRetriever
from ..rag.grounded_qa import GroundedQAPipeline
from ..storage.escalation_store import EscalationStore

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="Brilliant Directories Knowledge Brain API",
    description="Shared Enterprise Knowledge Service for AI Tech Consultant",
    version="1.0.0"
)

# Enable CORS for downstream Task 2 & Task 3 clients and Web Dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global State & Singletons
storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
crawler = PoliteCrawler(storage_dir=storage_dir)
chunker = DocumentChunker()
embedding_gen = get_embedding_generator()
vector_store = VectorStore(store_path=os.path.join(storage_dir, "vector_store.json"))
retriever = HybridRetriever(vector_store=vector_store)
escalation_store = EscalationStore(db_path=os.path.join(storage_dir, "escalations.db"))
qa_pipeline = GroundedQAPipeline(hybrid_retriever=retriever, escalation_store=escalation_store)


def index_article_files():
    """
    Scans storage/articles/ and indexes any unindexed articles into the vector store.
    """
    articles_dir = os.path.join(storage_dir, "articles")
    if not os.path.exists(articles_dir):
        return

    existing_urls = {c.get("url") for c in vector_store.chunks}
    new_chunks = []
    new_vectors = []

    for fname in os.listdir(articles_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(articles_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    art = json.load(f)
                    url = art.get("url")
                    if url not in existing_urls:
                        chunks = chunker.chunk_article(art)
                        for c in chunks:
                            vec = embedding_gen.embed_text(c["text"])
                            new_chunks.append(c)
                            new_vectors.append(vec)
            except Exception as e:
                logger.warning(f"Error indexing article {fname}: {e}")

    if new_chunks:
        vector_store.upsert_chunks(new_chunks, new_vectors)
        retriever._refresh_bm25()
        logger.info(f"Indexed {len(new_chunks)} new chunks into vector store.")


@app.on_event("startup")
def startup_event():
    logger.info("Initializing Knowledge Brain...")
    index_article_files()
    logger.info(f"Knowledge Brain ready with {vector_store.get_count()} chunks.")


@app.get("/health", response_model=HealthResponse)
def get_health():
    manifest_count = len(crawler.sitemap_parser.manifest)
    pending_esc = len(escalation_store.list_escalations(status="PENDING"))
    return {
        "status": "healthy",
        "service": "Knowledge Brain API",
        "version": "1.0.0",
        "indexed_chunks": vector_store.get_count(),
        "tracked_pages": manifest_count,
        "pending_escalations": pending_esc
    }


@app.post("/query", response_model=QueryResponse)
def query_knowledge_brain(req: QueryRequest):
    """
    Retrieve grounded answers with source citations from Brilliant Directories documentation.
    """
    try:
        result = qa_pipeline.query(
            question=req.question,
            top_k=req.top_k,
            auto_escalate=req.auto_escalate
        )
        return result
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal query processing error: {str(e)}")


def _run_crawler_task(max_pages: int, force_all: bool):
    try:
        crawler.run_ingestion(max_pages=max_pages, force_all=force_all)
        index_article_files()
    except Exception as e:
        logger.error(f"Background crawler failed: {e}", exc_info=True)


@app.post("/ingestion/run", response_model=IngestionResponse)
def trigger_ingestion(req: IngestionRequest, background_tasks: BackgroundTasks):
    """
    Triggers an async crawl job to ingest or update articles from the sitemap.
    """
    if crawler.is_running:
        return crawler.get_status()

    thread = threading.Thread(target=_run_crawler_task, args=(req.max_pages, req.force_all), daemon=True)
    thread.start()

    return crawler.get_status()


@app.get("/ingestion/status", response_model=IngestionResponse)
def get_ingestion_status():
    """
    Check current crawler progress and manifest stats.
    """
    return crawler.get_status()


@app.post("/escalations")
def create_escalation(req: EscalationCreateRequest):
    """
    Create a human expert escalation task for an unanswered question.
    """
    esc_id = escalation_store.create_escalation(
        question=req.question,
        reason=req.reason,
        evidence_snippets=req.evidence_snippets
    )
    return {"status": "success", "escalation_id": esc_id}


@app.get("/escalations", response_model=List[EscalationItem])
def list_escalations(status: Optional[str] = None):
    """
    List all pending or resolved expert escalations.
    """
    return escalation_store.list_escalations(status=status)


@app.post("/escalations/{escalation_id}/resolve")
def resolve_escalation(escalation_id: str, req: EscalationResolveRequest):
    """
    Expert submits an approved answer.
    The answer is saved into versioned expert knowledge and immediately indexed into retrieval.
    """
    try:
        result = escalation_store.resolve_escalation(
            escalation_id=escalation_id,
            expert_answer=req.expert_answer,
            expert_notes=req.expert_notes,
            approved_by=req.approved_by or "Senior Support Engineer"
        )

        # Index the expert answer as a chunk so future queries retrieve it
        expert_chunk = {
            "chunk_id": f"EXPERT_{escalation_id}",
            "title": f"Expert Approved Solution: {result['question'][:40]}",
            "url": f"https://support.brilliantdirectories.com/expert-solutions/{escalation_id}",
            "category": "Expert Solutions",
            "section_heading": "Verified Expert Resolution",
            "text": f"Question: {result['question']}\n\nExpert Verified Answer:\n{req.expert_answer}\nApproved by: {req.approved_by}",
            "images": []
        }
        vec = embedding_gen.embed_text(expert_chunk["text"])
        vector_store.upsert_chunks([expert_chunk], [vec])
        retriever._refresh_bm25()

        return {"status": "resolved", "data": result, "indexed": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving escalation {escalation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
