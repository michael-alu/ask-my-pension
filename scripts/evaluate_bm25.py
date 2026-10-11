"""
Evaluate the BM25 baseline retriever.

For every evaluation question, BM25 ranks all searchable passages. We check where the gold
passage landed. Results are reported for the validation and test splits, overall and broken
down by question origin (FAQ or own), source style (plain or legal) and level.

Writes:
- results/bm25_results.json        every summary
- results/bm25_predictions.jsonl   the top 10 for every question, for error analysis
- a row per split in results/experiments.csv and results/experiments.md

Run from the project root:
    python scripts/evaluate_bm25.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.eval_questions import load_eval_questions  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.retrieval import build_bm25, search_bm25  # noqa: E402
from src.retrieval_eval import TOP_K, evaluate_retriever  # noqa: E402
from src.splits import load_splits  # noqa: E402

RESULTS_FILE = PROJECT_ROOT / "results" / "bm25_results.json"

PREDICTIONS_FILE = PROJECT_ROOT / "results" / "bm25_predictions.jsonl"

EXPERIMENT_NAME = "BM25 retriever (baseline)"


def main() -> None:
    passages = load_searchable_passages()

    passages_by_id = {p["passage_id"]: p for p in passages}

    reading_ease = {p["passage_id"]: p["reading_ease"] for p in passages}

    questions = load_eval_questions(passages_by_id, load_splits())

    bm25 = build_bm25(passages)

    rankings = [search_bm25(bm25, passages, q["question"], TOP_K) for q in questions]

    evaluate_retriever(rankings, questions, reading_ease, EXPERIMENT_NAME, RESULTS_FILE, PREDICTIONS_FILE)


if __name__ == "__main__":
    main()
