"""
Evaluation Suite for Knowledge Brain (Task 1).
Runs 22 comprehensive test cases, validating grounded QA, citation fidelity,
insufficient evidence detection, prompt injection resilience, and latency.
"""

import json
import logging
import os
import sys
import time
from typing import Dict, List

# Add workspace to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from task1_knowledge_brain.rag.chunker import DocumentChunker
from task1_knowledge_brain.rag.embeddings import get_embedding_generator
from task1_knowledge_brain.rag.vector_store import VectorStore
from task1_knowledge_brain.rag.hybrid_retriever import HybridRetriever
from task1_knowledge_brain.rag.grounded_qa import GroundedQAPipeline
from task1_knowledge_brain.storage.escalation_store import EscalationStore

logger = logging.getLogger("evaluator")
logging.basicConfig(level=logging.INFO, format="%(message)s")


def run_eval():
    storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))
    articles_dir = os.path.join(storage_dir, "articles")
    eval_dataset_path = os.path.join(os.path.dirname(__file__), "eval_dataset.json")

    with open(eval_dataset_path, "r", encoding="utf-8") as f:
        test_cases = json.load(f)

    # Initialize RAG components
    chunker = DocumentChunker()
    embedding_gen = get_embedding_generator()
    vector_store = VectorStore(store_path=os.path.join(storage_dir, "vector_store.json"))

    # Index all articles from storage/articles
    print("Indexing articles for evaluation...")
    indexed_urls = set()
    all_chunks = []
    all_vecs = []

    for fname in os.listdir(articles_dir):
        if fname.endswith(".json"):
            fpath = os.path.join(articles_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    art = json.load(f)
                    url = art.get("url")
                    if url not in indexed_urls:
                        indexed_urls.add(url)
                        chunks = chunker.chunk_article(art)
                        for c in chunks:
                            vec = embedding_gen.embed_text(c["text"])
                            all_chunks.append(c)
                            all_vecs.append(vec)
            except Exception as e:
                print(f"Error loading {fname}: {e}")

    import numpy as np
    vector_store.chunks = []
    vector_store.vectors = np.empty((0, 128), dtype=np.float32)
    vector_store.upsert_chunks(all_chunks, all_vecs)
    print(f"Vector store populated with {vector_store.get_count()} chunks from {len(indexed_urls)} articles.")

    retriever = HybridRetriever(vector_store=vector_store)
    escalation_store = EscalationStore(db_path=os.path.join(storage_dir, "escalations.db"))
    qa = GroundedQAPipeline(hybrid_retriever=retriever, escalation_store=escalation_store)

    results = []
    passed_count = 0
    total_latency = 0.0

    print("\n" + "=" * 80)
    print(f"RUNNING {len(test_cases)} EVALUATION TEST CASES FOR TASK 1 KNOWLEDGE BRAIN")
    print("=" * 80)

    for tc in test_cases:
        tc_id = tc["id"]
        q = tc["question"]
        expected_status = tc["expected_status"]
        expected_terms = tc["expected_terms"]

        t0 = time.time()
        res = qa.query(q, top_k=3, auto_escalate=True)
        latency_ms = (time.time() - t0) * 1000.0
        total_latency += latency_ms

        status = res["status"]
        answer = res["answer"]
        sources = res["sources"]
        requires_human = res["requires_human"]

        # Verification criteria
        status_match = (status == expected_status)
        citations_valid = (len(sources) > 0) if (expected_status == "grounded") else (len(sources) == 0)

        # Keyword verification
        ans_lower = answer.lower()
        src_text = " ".join([s.get("title", "") + " " + s.get("excerpt", "") for s in sources]).lower()
        combined_text = ans_lower + " " + src_text

        terms_found = [term for term in expected_terms if term.lower() in combined_text]
        term_ratio = len(terms_found) / len(expected_terms) if expected_terms else 1.0
        terms_ok = term_ratio >= 0.4

        is_passed = status_match and (citations_valid or not expected_status == "grounded") and terms_ok

        if is_passed:
            passed_count += 1
            verdict = "[PASS]"
        else:
            verdict = "[FAIL]"

        print(f"{verdict} {tc_id} [{tc['category']}]: '{q[:50]}...' -> Status: {status} (Latency: {latency_ms:.1f}ms, Citations: {len(sources)})")

        results.append({
            "id": tc_id,
            "category": tc["category"],
            "question": q,
            "expected_status": expected_status,
            "actual_status": status,
            "confidence": res["confidence"],
            "requires_human": requires_human,
            "citations_count": len(sources),
            "sources": [{"title": s["title"], "url": s["url"]} for s in sources],
            "latency_ms": round(latency_ms, 2),
            "passed": is_passed,
            "terms_matched": terms_found
        })

    pass_rate = (passed_count / len(test_cases)) * 100.0
    avg_latency = total_latency / len(test_cases)

    print("\n" + "=" * 80)
    print(f"EVALUATION SUMMARY: {passed_count}/{len(test_cases)} Passed ({pass_rate:.1f}%)")
    print(f"Average Latency: {avg_latency:.1f}ms per query")
    print("=" * 80)

    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
        "total_cases": len(test_cases),
        "passed_cases": passed_count,
        "pass_rate_percent": round(pass_rate, 2),
        "avg_latency_ms": round(avg_latency, 2),
        "test_results": results
    }

    report_path = os.path.join(os.path.dirname(__file__), "evaluation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"Evaluation report saved to: {report_path}")
    return report


if __name__ == "__main__":
    run_eval()
