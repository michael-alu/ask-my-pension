"""
Dense retrieval: turn every passage and every question into an embedding (a list of numbers
that captures meaning), then rank passages by how close their embedding is to the question's.

Unlike BM25, this can match "move my pension to another PFA" with "RSA transfer", because the
two mean similar things even though they share no words.
"""

import numpy as np
from sentence_transformers import SentenceTransformer

from src.data_types import Passage


def load_dense_model(model_name: str) -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed(model: SentenceTransformer, texts: list[str]) -> np.ndarray:
    """One row per text. Normalised, so a dot product between two rows is their cosine similarity."""
    embeddings: np.ndarray = model.encode(texts, batch_size=32, normalize_embeddings=True, show_progress_bar=False)

    return embeddings


def search_dense_scored(
    model: SentenceTransformer, passage_embeddings: np.ndarray, passages: list[Passage], question: str, top_k: int
) -> list[tuple[str, float]]:
    """The top_k passage ids, best first, each with its similarity to the question (1 is identical)."""
    question_embedding = embed(model, [question])[0]

    similarities = passage_embeddings @ question_embedding

    best_positions = np.argsort(-similarities)[:top_k]

    return [(passages[position]["passage_id"], float(similarities[position])) for position in best_positions]


def search_dense(
    model: SentenceTransformer, passage_embeddings: np.ndarray, passages: list[Passage], question: str, top_k: int
) -> list[str]:
    scored = search_dense_scored(model, passage_embeddings, passages, question, top_k)

    return [passage_id for passage_id, _ in scored]
