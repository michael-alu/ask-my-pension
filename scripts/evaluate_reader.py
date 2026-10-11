"""
Evaluate a zero-shot reader: an off-the-shelf SQuAD 2.0 model with no extra training.

Three checks, on the validation and test splits:
1. Gold passage: the reader is given the right passage. This measures the reader alone.
2. End to end: BM25 finds the top 3 passages and the reader answers from them. This measures
   the whole system, the way a user experiences it.
3. Out of domain: the end-to-end system on questions that are not about pensions. The
   refusal rate is the share it correctly declines to answer.

Writes results/reader_<model>_results.json, results/reader_<model>_predictions.jsonl and rows
in the experiments table. Run export_squad.py first.

Run from the project root (the model name is optional):
    python scripts/evaluate_reader.py deepset/roberta-base-squad2
"""

import csv
import json
import statistics
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import Passage, SquadExample  # noqa: E402
from src.experiments import record_experiment  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.qa_metrics import qa_summary  # noqa: E402
from src.reader import decide, load_reader, read  # noqa: E402
from src.retrieval import build_bm25, search_bm25  # noqa: E402
from src.review_files import OUT_OF_DOMAIN_FILE  # noqa: E402

SQUAD_FOLDER = PROJECT_ROOT / "data" / "squad"

RESULTS_FOLDER = PROJECT_ROOT / "results"

DEFAULT_MODEL = "deepset/roberta-base-squad2"

THRESHOLD = 0.0

PASSAGES_TO_READ = 3


def read_examples(split: str) -> list[SquadExample]:
    with open(SQUAD_FOLDER / f"{split}.jsonl", encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def answer_from_passages(reader: Any, question: str, passages: list[Passage]) -> tuple[str, str | None]:
    """Read each passage and keep the most confident answer. Returns the answer and its passage id."""
    best_answer = ""

    best_passage_id = None

    best_margin = THRESHOLD

    for passage in passages:
        answer, answer_score, no_answer_score = read(reader, question, passage["text"])

        margin = answer_score - no_answer_score

        if decide(answer, answer_score, no_answer_score, THRESHOLD) and margin > best_margin:
            best_answer = answer

            best_passage_id = passage["passage_id"]

            best_margin = margin

    return best_answer, best_passage_id


def summarise_slices(rows: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    summaries = {"all": qa_summary([r["prediction"] for r in rows], [r["gold"] for r in rows])}

    for slice_name in ["origin", "style", "level"]:
        for value in sorted({r[slice_name] for r in rows}):
            group = [r for r in rows if r[slice_name] == value]

            summaries[f"{slice_name}={value}"] = qa_summary([r["prediction"] for r in group], [r["gold"] for r in group])

    return summaries


def main() -> None:
    model_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL

    short_name = model_name.split("/")[-1]

    reader = load_reader(model_name)

    passages = load_searchable_passages()

    passages_by_id = {p["passage_id"]: p for p in passages}

    bm25 = build_bm25(passages)

    results: dict[str, Any] = {"model": model_name, "threshold": THRESHOLD}

    predictions: list[dict[str, Any]] = []

    for split in ["validation", "test"]:
        gold_rows: list[dict[str, Any]] = []

        end_to_end_rows: list[dict[str, Any]] = []

        for example in read_examples(split):
            answer, answer_score, no_answer_score = read(reader, example["question"], example["context"])

            gold_answer = decide(answer, answer_score, no_answer_score, THRESHOLD)

            top_ids = search_bm25(bm25, passages, example["question"], PASSAGES_TO_READ)

            retrieved = [passages_by_id[passage_id] for passage_id in top_ids]

            e2e_answer, e2e_passage_id = answer_from_passages(reader, example["question"], retrieved)

            shared = {
                "id": example["id"],
                "question": example["question"],
                "gold": example["answer_text"],
                "origin": example["origin"],
                "style": example["style"],
                "level": example["level"],
            }

            gold_rows.append({**shared, "prediction": gold_answer})

            end_to_end_rows.append({**shared, "prediction": e2e_answer, "answer_passage_id": e2e_passage_id})

            predictions.append(
                {
                    **shared,
                    "split": split,
                    "gold_passage_prediction": gold_answer,
                    "end_to_end_prediction": e2e_answer,
                    "end_to_end_passage_id": e2e_passage_id,
                }
            )

        results[f"{split}/gold_passage"] = summarise_slices(gold_rows)

        results[f"{split}/end_to_end"] = summarise_slices(end_to_end_rows)

        answered_ease = [
            passages_by_id[r["answer_passage_id"]]["reading_ease"] for r in end_to_end_rows if r["answer_passage_id"]
        ]

        gold_all = results[f"{split}/gold_passage"]["all"]

        e2e_all = results[f"{split}/end_to_end"]["all"]

        record_experiment(
            {
                "experiment": f"Zero-shot reader {short_name}, gold passage",
                "split": split,
                "questions": gold_all["questions"],
                "exact_match": gold_all["exact_match"],
                "f1": gold_all["f1"],
                "notes": f"answerable F1 {gold_all['answerable_f1']}, no-answer accuracy {gold_all['no_answer_accuracy']}",
            }
        )

        e2e_row: dict[str, str | float | int] = {
            "experiment": f"BM25 + zero-shot reader {short_name}, end to end",
            "split": split,
            "questions": e2e_all["questions"],
            "exact_match": e2e_all["exact_match"],
            "f1": e2e_all["f1"],
            "notes": f"answerable F1 {e2e_all['answerable_f1']}, no-answer accuracy {e2e_all['no_answer_accuracy']}",
        }

        if answered_ease:
            e2e_row["top1_reading_ease"] = round(statistics.mean(answered_ease), 1)

        if split == "test":
            e2e_row["ood_refusal_rate"] = evaluate_out_of_domain(reader, bm25, passages, results)

        record_experiment(e2e_row)

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    (RESULTS_FOLDER / f"reader_{short_name}_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    with open(RESULTS_FOLDER / f"reader_{short_name}_predictions.jsonl", "w", encoding="utf-8") as file:
        for prediction in predictions:
            file.write(json.dumps(prediction, ensure_ascii=False) + "\n")

    print_summary(results)


def evaluate_out_of_domain(reader: Any, bm25: Any, passages: list[Passage], results: dict[str, Any]) -> float:
    with open(OUT_OF_DOMAIN_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    refused_by_distance: dict[str, list[float]] = {}

    examples = []

    for row in rows:
        top_ids = search_bm25(bm25, passages, row["question"], PASSAGES_TO_READ)

        retrieved = [p for p in passages if p["passage_id"] in top_ids]

        answer, passage_id = answer_from_passages(reader, row["question"], retrieved)

        refused = 1.0 if answer == "" else 0.0

        distance = row["distance"].strip().lower()

        refused_by_distance.setdefault(distance, []).append(refused)

        examples.append({"question": row["question"], "distance": distance, "answer": answer, "passage_id": passage_id})

    all_refusals = [value for values in refused_by_distance.values() for value in values]

    results["out_of_domain"] = {
        "refusal_rate": round(statistics.mean(all_refusals), 3),
        "by_distance": {d: round(statistics.mean(v), 3) for d, v in sorted(refused_by_distance.items())},
        "examples": examples,
    }

    return results["out_of_domain"]["refusal_rate"]


def print_summary(results: dict[str, Any]) -> None:
    print(f"model: {results['model']} | threshold: {results['threshold']}")

    print(f"{'setting / slice':44} {'n':>4} {'EM':>6} {'F1':>6} {'ans F1':>7} {'no-ans acc':>10}")

    for key, slices in results.items():
        if "/" not in key:
            continue

        for name, s in slices.items():
            print(
                f"{key + ' / ' + name:44} {s['questions']:>4.0f} {s['exact_match']:>6} {s['f1']:>6}"
                f" {s['answerable_f1']:>7} {s['no_answer_accuracy']:>10}"
            )

    ood = results["out_of_domain"]

    print(f"\nout-of-domain refusal rate: {ood['refusal_rate']} | by distance: {ood['by_distance']}")


if __name__ == "__main__":
    main()
