"""Clinical Local RAG Utility (Retrieval-Augmented Generation)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

class ClinicalDocumentIndex:
    """A lightweight, in-memory search index for clinical documents using TF-IDF."""

    def __init__(self, document_text: str, chunk_size: int = 500, overlap: int = 50):
        self.chunks = self._chunk_text(document_text, chunk_size, overlap)

        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(
                stop_words="english",
                ngram_range=(1, 2),
                max_df=0.95,
            )

            if self.chunks:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
                logger.info(f"Indexed {len(self.chunks)} document chunks.")
            else:
                self.tfidf_matrix = None
                logger.warning("Document text was empty, index not built.")
        except ImportError:
            logger.warning("scikit-learn is not installed. Indexing disabled.")
            self.tfidf_matrix = None

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        words = text.split()
        if not words:
            return []

        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i : i + chunk_size])
            chunks.append(chunk)
            i += chunk_size - overlap

        return chunks

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if self.tfidf_matrix is None or not self.chunks:
            return []

        try:
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
        except ImportError:
            return []

        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        if len(similarities) == 0:
            return []

        k = min(top_k, len(similarities))
        top_indices = np.argsort(similarities)[-k:][::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.01:
                results.append(
                    {
                        "chunk_id": int(idx),
                        "score": round(score, 4),
                        "text": self.chunks[idx],
                    }
                )

        return results

__all__ = ["ClinicalDocumentIndex"]
