"""
Score any retriever the same way, so BM25 and the dense retrievers are compared fairly.

Each retriever gives a ranked list of passage ids for every evaluation question. We check
where the gold passage landed, then summarise on the validation and test splits, overall and
by origin, style and level.
"""

import json
from pathlib import Path

from src.data_types import EvalQuestion, RetrievalPrediction
from src.experiments import record_experiment
from src.metrics import rank_of, retrieval_summary

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


def make_prediction(question: EvalQuestion, top_ids: list[str]) -> RetrievalPrediction:
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


def evaluate_retriever(
    rankings: list[list[str]],
    questions: list[EvalQuestion],
    reading_ease: dict[str, float],
    experiment_name: str,
    results_file: Path,
    predictions_file: Path,
) -> dict[str, dict[str, float]]:
    predictions = [make_prediction(question, top_ids) for question, top_ids in zip(questions, rankings)]

    results: dict[str, dict[str, float]] = {}

    for split in ["validation", "test"]:
        in_split = [p for p in predictions if p["split"] == split]

        results[f"{split}/all"] = summarise(in_split, reading_ease)

        for slice_name in SLICES:
            for value in sorted({slice_value(p, slice_name) for p in in_split}):
                group = [p for p in in_split if slice_value(p, slice_name) == value]

                results[f"{split}/{slice_name}={value}"] = summarise(group, reading_ease)

        record_experiment({"experiment": experiment_name, "split": split, **results[f"{split}/all"]})

    results_file.parent.mkdir(parents=True, exist_ok=True)

    results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")

    with open(predictions_file, "w", encoding="utf-8") as file:
        for prediction in predictions:
            file.write(json.dumps(prediction, ensure_ascii=False) + "\n")

    print(f"{experiment_name}")

    print(f"{'slice':32} {'n':>4} {'R@1':>6} {'R@5':>6} {'MRR@10':>7} {'top1 ease':>9}")

    for name, summary in results.items():
        print(
            f"{name:32} {summary['questions']:>4.0f} {summary['recall_at_1']:>6} {summary['recall_at_5']:>6}"
            f" {summary['mrr_at_10']:>7} {summary['top1_reading_ease']:>9}"
        )

    return results
