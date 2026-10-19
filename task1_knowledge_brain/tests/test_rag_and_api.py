"""
Unit and Integration Tests for Task 1 Knowledge Brain.
"""

import json
import os
import pytest
from fastapi.testclient import TestClient

from task1_knowledge_brain.api.app import app
from task1_knowledge_brain.crawler.article_parser import ArticleParser
from task1_knowledge_brain.rag.chunker import DocumentChunker
from task1_knowledge_brain.rag.embeddings import DenseEmbeddings
from task1_knowledge_brain.rag.vector_store import VectorStore
from task1_knowledge_brain.rag.hybrid_retriever import HybridRetriever
from task1_knowledge_brain.storage.escalation_store import EscalationStore

client = TestClient(app)


def test_article_parser():
    html = """
    <html>
      <head><title>Test Article | Knowledge Base</title></head>
      <body>
        <main>
          <h1>How to Setup Google Maps</h1>
          <p>Before configuring, make sure you have an API key.</p>
          <img src="https://example.com/screenshot.png" alt="Google Maps Key Form" />
          <h2>Step 1: Enter Credentials</h2>
          <ol>
            <li>Navigate to Settings > Integrations</li>
            <li>Paste your API Key</li>
            <li>Click Save Changes</li>
          </ol>
        </main>
      </body>
    </html>
    """
    parser = ArticleParser()
    res = parser.parse(html, "https://support.brilliantdirectories.com/test-article")
    assert res["title"] == "How to Setup Google Maps"
    assert len(res["images"]) == 1
    assert "Settings > Integrations" in res["images"][0]["surrounding_context"] or "API key" in res["images"][0]["surrounding_context"]
    assert len(res["procedural_steps"]) == 1
    assert len(res["procedural_steps"][0]) == 3


def test_chunker():
    chunker = DocumentChunker(target_chunk_size=100)
    article = {
        "title": "Test Title",
        "url": "https://example.com/article",
        "category": "Setup",
        "sections": [
            {"heading": "Intro", "content": "This is a quick intro text."},
            {"heading": "Steps", "content": "1. First step.\n2. Second step."}
        ],
        "enriched_images": []
    }
    chunks = chunker.chunk_article(article)
    assert len(chunks) >= 2
    assert chunks[0]["title"] == "Test Title"
    assert chunks[0]["url"] == "https://example.com/article"


def test_vector_store():
    store = VectorStore(store_path="task1_knowledge_brain/storage/test_vector_store.json")
    emb = DenseEmbeddings(dimension=128)
    
    chunk1 = {"chunk_id": "c1", "title": "Stripe Guide", "text": "Stripe credit card payments", "url": "http://a.com"}
    chunk2 = {"chunk_id": "c2", "title": "DNS Guide", "text": "Domain nameservers and records", "url": "http://b.com"}

    v1 = emb.embed_text(chunk1["text"])
    v2 = emb.embed_text(chunk2["text"])

    store.upsert_chunks([chunk1, chunk2], [v1, v2])
    assert store.get_count() >= 2

    # Query for Stripe
    q_vec = emb.embed_text("How to configure Stripe credit cards")
    results = store.search(q_vec, top_k=1)
    assert results[0][0]["chunk_id"] == "c1"

    # Cleanup test store file
    if os.path.exists("task1_knowledge_brain/storage/test_vector_store.json"):
        os.remove("task1_knowledge_brain/storage/test_vector_store.json")


def test_escalation_workflow():
    store = EscalationStore(db_path="task1_knowledge_brain/storage/test_esc.db")
    esc_id = store.create_escalation("How to configure custom quantum portal?", "No docs found")
    assert esc_id.startswith("ESC-")

    pending = store.list_escalations(status="PENDING")
    assert any(e["id"] == esc_id for e in pending)

    res = store.resolve_escalation(esc_id, "Quantum portal is not supported on this version.")
    assert res["status"] in ["RESOLVED", "resolved"]

    resolved = store.list_escalations(status="RESOLVED")
    assert any(e["id"] == esc_id for e in resolved)

    try:
        if os.path.exists("task1_knowledge_brain/storage/test_esc.db"):
            os.remove("task1_knowledge_brain/storage/test_esc.db")
    except Exception:
        pass


def test_api_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Knowledge Brain API"


def test_api_query_grounded():
    resp = client.post("/query", json={
        "question": "How do I configure Stripe payment gateway in Brilliant Directories?",
        "top_k": 3
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "grounded"
    assert len(data["sources"]) > 0
    assert "stripe" in data["answer"].lower() or "payment" in data["answer"].lower()


def test_api_query_insufficient_evidence():
    resp = client.post("/query", json={
        "question": "What is the secret interstellar hyperspace velocity formula?",
        "top_k": 3,
        "auto_escalate": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "insufficient_evidence"
    assert data["requires_human"] is True
    assert data["escalation_id"] is not None
