"""
BM25: the baseline retriever. It scores every passage by how many of the question's words it
contains, giving more weight to rare words (like "annuity") than common ones (like "the").
"""

import re

from rank_bm25 import BM25Okapi

from src.data_types import Passage


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def build_bm25(passages: list[Passage]) -> BM25Okapi:
    return BM25Okapi([tokenize(p["text"]) for p in passages])


def search_bm25(bm25: BM25Okapi, passages: list[Passage], question: str, top_k: int) -> list[str]:
    """Return the ids of the top_k passages, best first."""
    scores = bm25.get_scores(tokenize(question))

    positions = sorted(range(len(passages)), key=lambda position: scores[position], reverse=True)

    return [passages[position]["passage_id"] for position in positions[:top_k]]
