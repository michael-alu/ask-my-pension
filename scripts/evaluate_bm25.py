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

import json
import sys
from pathlib import Path

from rank_bm25 import BM25Okapi

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import EvalQuestion, Passage, RetrievalPrediction  # noqa: E402
from src.eval_questions import load_eval_questions  # noqa: E402
from src.experiments import record_experiment  # noqa: E402
from src.metrics import rank_of, retrieval_summary  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.retrieval import build_bm25, search_bm25  # noqa: E402
from src.splits import load_splits  # noqa: E402

RESULTS_FILE = PROJECT_ROOT / "results" / "bm25_results.json"

PREDICTIONS_FILE = PROJECT_ROOT / "results" / "bm25_predictions.jsonl"

EXPERIMENT_NAME = "BM25 retriever (baseline)"

TOP_K = 10

SLICES = ["origin", "style", "level"]


def summarise(predictions: list[RetrievalPrediction], reading_ease: dict[str, float]) -> dict[str, float]:
    ranks = [p["rank"] for p in predictions]

    top1_reading_ease = [reading_ease[p["top_ids"][0]] for p in predictions]

    return retrieval_summary(ranks, top1_reading_ease)


def slice_value(prediction: RetrievalPrediction, slice_name: str) -> str:
    if slice_name == "origin":
        return prediction["origin"]

    if slice_name == "style":
        return prediction["style"]

    return prediction["level"]


def predict(bm25: BM25Okapi, passages: list[Passage], question: EvalQuestion) -> RetrievalPrediction:
    top_ids = search_bm25(bm25, passages, question["question"], TOP_K)

    return {
        "question": question["question"],
        "gold_passage_id": question["gold_passage_id"],
        "origin": question["origin"],
        "level": question["level"],
        "split": question["split"],
        "style": question["style"],
        "top_ids": top_ids,
        "rank": rank_of(top_ids, question["gold_passage_id"]),
    }


def main() -> None:
    passages = load_searchable_passages()

    passages_by_id = {p["passage_id"]: p for p in passages}

    reading_ease = {p["passage_id"]: p["reading_ease"] for p in passages}

    questions: list[EvalQuestion] = load_eval_questions(passages_by_id, load_splits())

    bm25 = build_bm25(passages)

    predictions = [predict(bm25, passages, question) for question in questions]

    results: dict[str, dict[str, float]] = {}

    for split in ["validation", "test"]:
        in_split = [p for p in predictions if p["split"] == split]

        results[f"{split}/all"] = summarise(in_split, reading_ease)

        for slice_name in SLICES:
            for value in sorted({slice_value(p, slice_name) for p in in_split}):
                group = [p for p in in_split if slice_value(p, slice_name) == value]

                results[f"{split}/{slice_name}={value}"] = summarise(group, reading_ease)

        record_experiment({"experiment": EXPERIMENT_NAME, "split": split, **results[f"{split}/all"]})

    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

    RESULTS_FILE.write_text(json.dumps(results, indent=2), encoding="utf-8")

    with open(PREDICTIONS_FILE, "w", encoding="utf-8") as file:
        for prediction in predictions:
            file.write(json.dumps(prediction, ensure_ascii=False) + "\n")

    print(f"{'slice':32} {'n':>4} {'R@1':>6} {'R@5':>6} {'MRR@10':>7} {'top1 ease':>9}")

    for name, summary in results.items():
        print(
            f"{name:32} {summary['questions']:>4.0f} {summary['recall_at_1']:>6} {summary['recall_at_5']:>6}"
            f" {summary['mrr_at_10']:>7} {summary['top1_reading_ease']:>9}"
        )


if __name__ == "__main__":
    main()
