"""
Vector Store for Knowledge Brain.
Stores chunk metadata and vector embeddings with Cosine Similarity indexing,
upsert, and delete operations.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(self, store_path: str = "task1_knowledge_brain/storage/vector_store.json"):
        self.store_path = store_path
        os.makedirs(os.path.dirname(self.store_path), exist_ok=True)
        self.chunks: List[dict] = []
        self.vectors: np.ndarray = np.empty((0, 128), dtype=np.float32)
        self.load()

    def load(self) -> None:
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                    vec_list = data.get("vectors", [])
                    if vec_list:
                        self.vectors = np.array(vec_list, dtype=np.float32)
                    else:
                        self.vectors = np.empty((0, 128), dtype=np.float32)
                logger.info(f"Loaded {len(self.chunks)} chunks from vector store.")
            except Exception as e:
                logger.warning(f"Error loading vector store from {self.store_path}: {e}")
                self.chunks = []
                self.vectors = np.empty((0, 128), dtype=np.float32)

    def save(self) -> None:
        try:
            with open(self.store_path, "w", encoding="utf-8") as f:
                json.dump({
                    "chunks": self.chunks,
                    "vectors": self.vectors.tolist()
                }, f, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")

    def upsert_chunks(self, new_chunks: List[dict], new_vectors: List[List[float]]) -> None:
        """
        Add or replace chunks by chunk_id.
        """
        if not new_chunks:
            return

        chunk_id_to_idx = {c["chunk_id"]: i for i, c in enumerate(self.chunks)}
        
        to_append_chunks = []
        to_append_vecs = []

        for chunk, vec in zip(new_chunks, new_vectors):
            cid = chunk["chunk_id"]
            if cid in chunk_id_to_idx:
                idx = chunk_id_to_idx[cid]
                self.chunks[idx] = chunk
                self.vectors[idx] = np.array(vec, dtype=np.float32)
            else:
                to_append_chunks.append(chunk)
                to_append_vecs.append(vec)

        if to_append_chunks:
            self.chunks.extend(to_append_chunks)
            if self.vectors is None or self.vectors.shape[0] == 0:
                self.vectors = np.array(to_append_vecs, dtype=np.float32)
            else:
                self.vectors = np.vstack([self.vectors, np.array(to_append_vecs, dtype=np.float32)])

        self.save()

    def delete_by_url(self, url: str) -> int:
        """
        Remove all chunks belonging to a given article URL.
        """
        keep_indices = [i for i, c in enumerate(self.chunks) if c.get("url") != url]
        deleted_count = len(self.chunks) - len(keep_indices)
        if deleted_count > 0:
            self.chunks = [self.chunks[i] for i in keep_indices]
            if len(keep_indices) > 0 and self.vectors.shape[0] > 0:
                self.vectors = self.vectors[keep_indices]
            else:
                self.vectors = np.empty((0, 128), dtype=np.float32)
            self.save()
            logger.info(f"Deleted {deleted_count} chunks for URL: {url}")
        return deleted_count

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Tuple[dict, float]]:
        """
        Cosine similarity search. Returns list of (chunk_dict, score).
        """
        if len(self.chunks) == 0 or self.vectors.shape[0] == 0:
            return []

        q_vec = np.array(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []
        q_vec = q_vec / q_norm

        # Matrix dot product
        scores = np.dot(self.vectors, q_vec)
        
        # Get top indices
        top_k = min(top_k, len(self.chunks))
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            results.append((self.chunks[idx], float(scores[idx])))

        return results

    def get_count(self) -> int:
        return len(self.chunks)
