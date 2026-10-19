"""
Hybrid Retriever for Knowledge Brain.
Fuses Dense Semantic Search with BM25 Keyword Matching via Reciprocal Rank Fusion (RRF)
and incorporates Multimodal Screenshot relevance boosting.
"""

import math
import re
from typing import Dict, List, Tuple
from .embeddings import get_embedding_generator
from .vector_store import VectorStore


class BM25Index:
    def __init__(self, chunks: List[dict]):
        self.chunks = chunks
        self.corpus_size = len(chunks)
        self.doc_len = []
        self.avg_doc_len = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs: List[Dict[str, int]] = []
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())

    def _build_index(self):
        total_len = 0
        for chunk in self.chunks:
            tokens = self._tokenize(chunk.get("text", "") + " " + chunk.get("title", ""))
            self.doc_len.append(len(tokens))
            total_len += len(tokens)

            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs.append(tf)

            for t in tf.keys():
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = (total_len / self.corpus_size) if self.corpus_size > 0 else 1.0

    def search(self, query: str, top_k: int = 10, k1: float = 1.5, b: float = 0.75) -> List[Tuple[dict, float]]:
        if self.corpus_size == 0:
            return []

        q_tokens = self._tokenize(query)
        scores = [0.0] * self.corpus_size

        for token in q_tokens:
            if token not in self.doc_freqs:
                continue

            # IDF calculation with smoothing
            df = self.doc_freqs[token]
            idf = math.log(1.0 + (self.corpus_size - df + 0.5) / (df + 0.5))

            for i in range(self.corpus_size):
                tf = self.term_freqs[i].get(token, 0)
                if tf == 0:
                    continue
                d_len = self.doc_len[i]
                numerator = tf * (k1 + 1.0)
                denominator = tf + k1 * (1.0 - b + b * (d_len / self.avg_doc_len))
                scores[i] += idf * (numerator / denominator)

        # Rank
        ranked_indices = sorted(range(self.corpus_size), key=lambda i: scores[i], reverse=True)[:top_k]
        results = []
        for idx in ranked_indices:
            if scores[idx] > 0.0:
                results.append((self.chunks[idx], scores[idx]))
        return results


class HybridRetriever:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.embedding_generator = get_embedding_generator()
        self.bm25_index = None
        self._refresh_bm25()

    def _refresh_bm25(self):
        self.bm25_index = BM25Index(self.vector_store.chunks)

    def retrieve(self, query: str, top_k: int = 5, min_relevance_threshold: float = 0.25) -> List[dict]:
        """
        Hybrid retrieval combining Dense Vector Search + BM25 using Reciprocal Rank Fusion.
        """
        if self.vector_store.get_count() == 0:
            return []

        # Refresh BM25 if chunk counts changed
        if len(self.bm25_index.chunks) != len(self.vector_store.chunks):
            self._refresh_bm25()

        # 1. Dense Semantic Search
        q_vec = self.embedding_generator.embed_text(query)
        dense_results = self.vector_store.search(q_vec, top_k=top_k * 2)

        # 2. BM25 Keyword Search
        bm25_results = self.bm25_index.search(query, top_k=top_k * 2)

        # Filter candidates by minimum relevance
        dense_map = {chunk["chunk_id"]: score for chunk, score in dense_results if score >= 0.22}
        bm25_map = {chunk["chunk_id"]: score for chunk, score in bm25_results if score >= 0.5}

        # Candidate pool is union of chunks with meaningful signal
        all_candidate_cids = set(dense_map.keys()) | set(bm25_map.keys())
        if not all_candidate_cids:
            return []

        fused_scores: Dict[str, float] = {}
        chunk_map: Dict[str, dict] = {}

        for chunk, score in dense_results:
            cid = chunk["chunk_id"]
            if cid in all_candidate_cids:
                chunk_map[cid] = chunk

        for chunk, score in bm25_results:
            cid = chunk["chunk_id"]
            if cid in all_candidate_cids:
                chunk_map[cid] = chunk

        # RRF and score calibration
        rrf_k = 60
        for rank, (chunk, score) in enumerate(dense_results, start=1):
            cid = chunk["chunk_id"]
            if cid in all_candidate_cids:
                dense_weight = max(0.0, score)
                fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank)) * 0.5 * dense_weight

        for rank, (chunk, score) in enumerate(bm25_results, start=1):
            cid = chunk["chunk_id"]
            if cid in all_candidate_cids:
                bm25_weight = min(score / 5.0, 1.0)
                fused_scores[cid] = fused_scores.get(cid, 0.0) + (1.0 / (rrf_k + rank)) * 0.5 * bm25_weight

        # Multimodal Screenshot Boost
        q_lower = query.lower()
        for cid in list(fused_scores.keys()):
            chunk = chunk_map[cid]
            images = chunk.get("images", [])
            for img in images:
                labels = img.get("labels", []) or img.get("interface_labels", [])
                if any(lbl.lower() in q_lower for lbl in labels if len(lbl) > 2):
                    fused_scores[cid] += 0.005

        # Sort by fused score
        sorted_cids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)

        results = []
        for cid in sorted_cids[:top_k]:
            chunk = chunk_map[cid]
            d_score = dense_map.get(cid, 0.0)
            b_score = min(bm25_map.get(cid, 0.0) / 8.0, 1.0)
            calibrated_score = round(max(d_score * 0.6 + b_score * 0.4, 0.0), 3)

            results.append({
                "chunk": chunk,
                "relevance_score": calibrated_score,
                "is_confident": calibrated_score >= min_relevance_threshold
            })

        return results
