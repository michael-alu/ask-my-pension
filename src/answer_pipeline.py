"""
The whole Ask My Pension system in one place: a question goes in, an answer comes out.

1. The fine-tuned retriever finds the 30 passages closest in meaning to the question.
2. Plain passages get a small boost (0.02), so they win close calls against legal passages.
3. The fine-tuned reader reads the top 3 and keeps its most confident answer.
4. If no answer beats "no answer" by the threshold tuned on validation, the system politely refuses.

These are the same pieces, settings and models that were evaluated in the experiments table.
"""

import csv
import json
from pathlib import Path
from typing import Any, TypedDict

import numpy as np

from src.data_types import Passage
from src.dense_retrieval import embed, load_dense_model, search_dense_scored
from src.glossary import GlossaryEntry, load_glossary, terms_in
from src.passages import load_searchable_passages
from src.plain_boost import APP_BOOST, rerank_with_plain_boost
from src.reader import decide_across_passages, load_reader, read

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RETRIEVER_FOLDER = PROJECT_ROOT / "models" / "retriever-bge-small-en-v1.5-100pct"

READER_FOLDER = PROJECT_ROOT / "models" / "reader-roberta-base-squad2-100pct-matched"

THRESHOLD_FILE = (
    PROJECT_ROOT / "results" / "reader_reader-roberta-base-squad2-100pct-matched_retriever-bge-small-en-v1.5-100pct_results.json"
)

EMBEDDINGS_FILE = PROJECT_ROOT / "models" / "passage_embeddings.npy"

SOURCES_FILE = PROJECT_ROOT / "data" / "sources.csv"

CANDIDATES = 30

PASSAGES_TO_READ = 3


class Source(TypedDict):
    title: str
    publisher: str
    url: str


class System(TypedDict):
    retriever: Any
    reader: Any
    passages: list[Passage]
    passages_by_id: dict[str, Passage]
    styles: dict[str, str]
    embeddings: np.ndarray
    threshold: float
    sources: dict[str, Source]
    glossary: list[GlossaryEntry]


class Answer(TypedDict):
    answer: str
    passage_text: str
    section: str
    source: Source | None
    glossary: list[GlossaryEntry]


def load_sources() -> dict[str, Source]:
    with open(SOURCES_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    return {row["source_id"]: {"title": row["title"], "publisher": row["publisher"], "url": row["url"]} for row in rows}


def load_passage_embeddings(retriever: Any, passages: list[Passage]) -> np.ndarray:
    """Embedding 1,559 passages takes minutes on a CPU, so it is done once and saved."""
    if EMBEDDINGS_FILE.exists():
        saved: np.ndarray = np.load(EMBEDDINGS_FILE)

        if saved.shape[0] == len(passages):
            return saved

    embeddings = embed(retriever, [p["text"] for p in passages])

    np.save(EMBEDDINGS_FILE, embeddings)

    return embeddings


def load_system() -> System:
    passages = load_searchable_passages()

    retriever = load_dense_model(str(RETRIEVER_FOLDER))

    tuned: float = json.loads(THRESHOLD_FILE.read_text(encoding="utf-8"))["tuned_threshold"]

    return {
        "retriever": retriever,
        "reader": load_reader(str(READER_FOLDER)),
        "passages": passages,
        "passages_by_id": {p["passage_id"]: p for p in passages},
        "styles": {p["passage_id"]: p["style"] for p in passages},
        "embeddings": load_passage_embeddings(retriever, passages),
        "threshold": tuned,
        "sources": load_sources(),
        "glossary": load_glossary(),
    }


def answer_question(system: System, question: str) -> Answer:
    scored = search_dense_scored(system["retriever"], system["embeddings"], system["passages"], question, CANDIDATES)

    top_ids = rerank_with_plain_boost(scored, system["styles"], APP_BOOST)[:PASSAGES_TO_READ]

    reads = []

    for passage_id in top_ids:
        answer, margin = read(system["reader"], question, system["passages_by_id"][passage_id]["text"])

        reads.append((answer, margin, passage_id))

    best_answer, best_passage_id = decide_across_passages(reads, system["threshold"])

    if best_passage_id is None:
        return {"answer": "", "passage_text": "", "section": "", "source": None, "glossary": []}

    passage = system["passages_by_id"][best_passage_id]

    return {
        "answer": best_answer,
        "passage_text": passage["text"],
        "section": passage["section"],
        "source": system["sources"].get(passage["source_id"]),
        "glossary": terms_in(best_answer + " " + passage["text"], system["glossary"]),
    }
