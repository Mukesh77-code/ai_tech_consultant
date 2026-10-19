"""
Grounded QA Pipeline for Knowledge Brain.
Synthesizes answers strictly supported by retrieved evidence, enforces citation attribution,
detects insufficient evidence, sanitizes against prompt injection, and flags human escalations.
"""

import json
import logging
import os
import re
from typing import Dict, List, Optional
import requests

from .hybrid_retriever import HybridRetriever
from ..storage.escalation_store import EscalationStore

logger = logging.getLogger(__name__)


class GroundedQAPipeline:
    def __init__(self, hybrid_retriever: HybridRetriever, escalation_store: EscalationStore):
        self.retriever = hybrid_retriever
        self.escalation_store = escalation_store
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

    def _sanitize_input(self, text: str) -> str:
        """
        Sanitize prompt injection attempts in customer queries.
        """
        # Block common prompt injection patterns
        patterns = [
            r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
            r"disregard\s+(the\s+)?above",
            r"system\s*prompt\s*injection",
            r"you\s+are\s+now\s+a",
            r"jailbreak",
            r"reveal\s+your\s+instructions"
        ]
        clean = text
        for p in patterns:
            clean = re.sub(p, "[FILTERED_INJECTION]", clean, flags=re.I)
        return clean.strip()

    def query(self, question: str, top_k: int = 4, auto_escalate: bool = False) -> dict:
        """
        Executes grounded retrieval and QA pipeline.
        Returns typed grounded response with citations and confidence.
        """
        sanitized_q = self._sanitize_input(question)
        if "[FILTERED_INJECTION]" in sanitized_q:
            return {
                "question": question,
                "answer": "Security alert: The query contains disallowed instruction overrides and was rejected. Insufficient grounded evidence.",
                "confidence": 0.05,
                "status": "insufficient_evidence",
                "requires_human": True,
                "escalation_id": None,
                "sources": []
            }

        retrieved = self.retriever.retrieve(sanitized_q, top_k=top_k)

        # Distinctive keyword coverage check to filter out false positive stopword matches
        stopwords = {
            "brilliant", "directories", "directory", "what", "when", "where",
            "which", "how", "does", "can", "with", "from", "that", "this",
            "your", "have", "used", "exact", "using", "into", "ours", "their", "will"
        }
        tokens = [w for w in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", sanitized_q.lower()) if w not in stopwords]
        
        evidence_matched = False
        if tokens and retrieved:
            for item in retrieved:
                doc_text = (item["chunk"].get("text", "") + " " + item["chunk"].get("title", "")).lower()
                matches = sum(1 for t in tokens if t in doc_text)
                if (len(tokens) <= 2 and matches >= 1) or (len(tokens) > 2 and matches >= 2 and matches / len(tokens) >= 0.35):
                    evidence_matched = True
                    break
        else:
            evidence_matched = bool(retrieved)

        # 1. Check if evidence is sufficient
        if not retrieved or not evidence_matched or all(r["relevance_score"] < 0.28 for r in retrieved):
            esc_id = None
            if auto_escalate:
                esc_id = self.escalation_store.create_escalation(
                    question=sanitized_q,
                    reason="Insufficient evidence in knowledge base",
                    evidence_snippets=[]
                )

            return {
                "question": question,
                "answer": (
                    "I searched the Brilliant Directories Solution Center documentation, but there is "
                    "insufficient information to reliably answer this question. The request has been flagged "
                    "for human expert review."
                ),
                "confidence": 0.15,
                "status": "insufficient_evidence",
                "requires_human": True,
                "escalation_id": esc_id,
                "sources": []
            }

        # Filter confident evidence
        confident_results = [r for r in retrieved if r["relevance_score"] >= 0.22]
        if not confident_results:
            confident_results = retrieved[:2]

        # Extract citations
        sources = []
        evidence_texts = []
        seen_urls = set()

        for item in confident_results:
            chunk = item["chunk"]
            url = chunk.get("url")
            excerpt = chunk.get("text", "")[:350]
            img_ref = None
            if chunk.get("images"):
                img_ref = chunk["images"][0].get("url") or chunk["images"][0].get("image_url")

            if url not in seen_urls:
                seen_urls.add(url)
                sources.append({
                    "title": chunk.get("title", "Article"),
                    "url": url,
                    "section": chunk.get("section_heading", ""),
                    "excerpt": excerpt,
                    "image_url": img_ref
                })
            evidence_texts.append(f"[{chunk.get('title')} | {chunk.get('section_heading')}]:\n{chunk.get('text')}")

        combined_evidence = "\n\n---\n\n".join(evidence_texts)

        # 2. Synthesize answer
        answer = None
        if self.anthropic_api_key:
            answer = self._generate_with_claude(sanitized_q, combined_evidence, sources)

        if not answer:
            answer = self._generate_grounded_local(sanitized_q, confident_results, sources)

        # Compute calibrated confidence
        avg_score = sum(r["relevance_score"] for r in confident_results) / len(confident_results)
        calibrated_conf = round(min(0.96, avg_score * 0.95), 2)

        return {
            "question": question,
            "answer": answer,
            "confidence": calibrated_conf,
            "status": "grounded",
            "requires_human": False,
            "escalation_id": None,
            "sources": sources
        }

    def _generate_with_claude(self, question: str, evidence: str, sources: list) -> Optional[str]:
        try:
            prompt = (
                f"You are the Brilliant Directories AI Knowledge Brain. Answer the question based ONLY on the evidence below.\n"
                f"Cite the source article titles and settings paths.\n"
                f"If the evidence does not fully answer the question, state what is missing rather than guessing.\n\n"
                f"Question: {question}\n\n"
                f"Evidence:\n{evidence}"
            )
            headers = {
                "x-api-key": self.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 400,
                "messages": [{"role": "user", "content": prompt}]
            }
            res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=20)
            if res.status_code == 200:
                data = res.json()
                return data["content"][0]["text"]
        except Exception as e:
            logger.warning(f"Claude answer generation fallback: {e}")
        return None

    def _generate_grounded_local(self, question: str, candidate_results: list, sources: list) -> str:
        """
        High-fidelity deterministic grounded synthesizer extracting factual statements,
        ordered steps, and settings paths directly from the retrieved chunks.
        """
        top_chunk = candidate_results[0]["chunk"]
        title = top_chunk.get("title", "Article")
        text = top_chunk.get("text", "")

        # Look for step-by-step numbers or bullet lists
        steps = re.findall(r"(?:\d+\.\s+[^\n]+)", text)
        sentences = [s.strip() for s in re.split(r"[.\n]", text) if len(s.strip()) > 25]

        # Filter sentences relevant to question words
        q_words = set(re.findall(r"\b\w{3,}\b", question.lower()))
        matched_sentences = []
        for s in sentences:
            if any(w in s.lower() for w in q_words):
                matched_sentences.append(s)

        response_lines = [f"Based on the Brilliant Directories documentation in **{title}**:"]

        if steps:
            response_lines.append("\nRecommended steps:")
            for s in steps[:5]:
                response_lines.append(f"- {s.strip()}")
        elif matched_sentences:
            response_lines.append("\n" + ". ".join(matched_sentences[:3]) + ".")
        else:
            # Fallback to leading summary
            clean_body = re.sub(r"Article:.*?\n", "", text)
            clean_body = re.sub(r"Category:.*?\n", "", clean_body)
            clean_body = re.sub(r"Section:.*?\n", "", clean_body).strip()
            summary = clean_body[:300].strip()
            response_lines.append(f"\n{summary}...")

        # Add visual reference if screenshot is present
        if top_chunk.get("images"):
            img = top_chunk["images"][0]
            if img.get("labels") or img.get("interface_labels"):
                labels = img.get("labels") or img.get("interface_labels")
                response_lines.append(f"\n*Interface Reference*: Look for UI controls: **{', '.join(labels[:4])}**.")

        # Source citations note
        response_lines.append(f"\n\n*Source: [{title}]({top_chunk.get('url')})*")

        return "\n".join(response_lines)
