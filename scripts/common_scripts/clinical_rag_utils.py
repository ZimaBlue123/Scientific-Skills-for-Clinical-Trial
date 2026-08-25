"""
Clinical Local RAG Utility (Retrieval-Augmented Generation)

A lightweight vector-search implementation utilizing scikit-learn's TF-IDF
and Cosine Similarity to search through massive clinical documents
(e.g., Clinical Study Reports, Investigator's Brochures, or EDC exports).

This avoids feeding entire 200+ page documents to an LLM, reducing
hallucinations, token costs, and context limits.

Usage:
    from common_scripts.clinical_rag_utils import ClinicalDocumentIndex

    # 1. Initialize with text
    index = ClinicalDocumentIndex(massive_text, chunk_size=500)

    # 2. Search for relevant sections
    results = index.search("Grade 3 adverse events fever", top_k=3)
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

LOGGER = logging.getLogger(__name__)


class ClinicalDocumentIndex:
    """
    A lightweight, in-memory search index for clinical documents.
    Uses TF-IDF for fast, keyword/semantic-adjacent retrieval without requiring heavy Neural Networks.
    """

    def __init__(self, document_text: str, chunk_size: int = 500, overlap: int = 50):
        self.chunks = self._chunk_text(document_text, chunk_size, overlap)
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),  # Capture bigrams like "adverse event"
            max_df=0.95,
        )

        if self.chunks:
            self.tfidf_matrix = self.vectorizer.fit_transform(self.chunks)
            LOGGER.info(f"Indexed {len(self.chunks)} document chunks.")
        else:
            self.tfidf_matrix = None
            LOGGER.warning("Document text was empty, index not built.")

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """
        Splits a massive text string into sliding windows of words.
        """
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
        """
        Search the document for the query and return the top_k most relevant chunks.
        """
        if self.tfidf_matrix is None or not self.chunks:
            return []

        # Vectorize the query
        query_vec = self.vectorizer.transform([query])

        # Calculate cosine similarity between query and all chunks
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        # Get top K indices
        if len(similarities) == 0:
            return []

        # Handle cases where top_k > number of chunks
        k = min(top_k, len(similarities))

        # np.argsort returns ascending, so we reverse it to get descending
        top_indices = np.argsort(similarities)[-k:][::-1]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            # Optional: filter out completely irrelevant matches
            if score > 0.01:
                results.append(
                    {
                        "chunk_id": int(idx),
                        "score": round(score, 4),
                        "text": self.chunks[idx],
                    }
                )

        return results
