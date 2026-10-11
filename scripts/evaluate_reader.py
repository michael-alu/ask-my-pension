"""
Evaluate a reader, off the shelf (zero-shot) or fine-tuned by train_reader.py.

Three checks:
1. Gold passage: the reader is given the right passage. This measures the reader alone.
2. End to end: a retriever finds the top 3 passages and the reader answers from them. This
   measures the whole system, the way a user experiences it.
3. Out of domain: the end-to-end system on questions that are not about pensions. The refusal
   rate is the share it correctly declines to answer.

The no-answer threshold is tuned on the validation split (the one with the best F1), then
applied unchanged to test. The model is run once and its raw margins are kept, so trying many
thresholds is fast.

Writes results/reader_<reader>_<retriever>_results.json, a predictions file, and test rows in
the experiments table. Run export_squad.py first.

Run from the project root. The reader defaults to roberta-base-squad2 and the retriever to BM25:
    python scripts/evaluate_reader.py deepset/roberta-base-squad2
    python scripts/evaluate_reader.py models/reader-roberta-base-squad2-100pct models/retriever-bge-small-en-v1.5-100pct
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
from src.dense_retrieval import embed, load_dense_model, search_dense  # noqa: E402
from src.experiments import record_experiment  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.qa_metrics import qa_summary  # noqa: E402
from src.reader import decide, decide_across_passages, load_reader, read  # noqa: E402
from src.retrieval import build_bm25, search_bm25  # noqa: E402
from src.review_files import OUT_OF_DOMAIN_FILE  # noqa: E402

SQUAD_FOLDER = PROJECT_ROOT / "data" / "squad"

RESULTS_FOLDER = PROJECT_ROOT / "results"

PASSAGES_TO_READ = 3

THRESHOLDS = [round(-1.0 + step * 0.05, 2) for step in range(41)]

SLICES = ["origin", "style", "level"]


def short_name_of(model_name: str) -> str:
    return model_name.rstrip("/").split("/")[-1]


def read_examples(split: str) -> list[SquadExample]:
    with open(SQUAD_FOLDER / f"{split}.jsonl", encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def retrieve_all(retriever_name: str, passages: list[Passage], questions: list[str]) -> list[list[str]]:
    """The top passages for every question, from BM25 or a dense model."""
    if retriever_name == "bm25":
        bm25 = build_bm25(passages)

        return [search_bm25(bm25, passages, question, PASSAGES_TO_READ) for question in questions]

    model = load_dense_model(retriever_name)

    passage_embeddings = embed(model, [p["text"] for p in passages])

    return [search_dense(model, passage_embeddings, passages, question, PASSAGES_TO_READ) for question in questions]


def raw_reads(reader: Any, example: SquadExample, retrieved: list[Passage]) -> dict[str, Any]:
    gold_answer, gold_margin = read(reader, example["question"], example["context"])

    end_to_end = []

    for passage in retrieved:
        answer, margin = read(reader, example["question"], passage["text"])

        end_to_end.append((answer, margin, passage["passage_id"]))

    return {
        "id": example["id"],
        "question": example["question"],
        "gold": example["answer_text"],
        "origin": example["origin"],
        "style": example["style"],
        "level": example["level"],
        "gold_read": (gold_answer, gold_margin),
        "end_to_end_reads": end_to_end,
    }


def gold_predictions(rows: list[dict[str, Any]], threshold: float) -> list[str]:
    return [decide(row["gold_read"][0], row["gold_read"][1], threshold) for row in rows]


def end_to_end_predictions(rows: list[dict[str, Any]], threshold: float) -> list[tuple[str, str | None]]:
    return [decide_across_passages(row["end_to_end_reads"], threshold) for row in rows]


def best_threshold(validation_rows: list[dict[str, Any]]) -> float:
    """The threshold with the best gold-passage F1 on validation. Ties go to the one closest to 0."""
    golds = [row["gold"] for row in validation_rows]

    scored = []

    for threshold in THRESHOLDS:
        f1 = qa_summary(gold_predictions(validation_rows, threshold), golds)["f1"]

        scored.append((f1, -abs(threshold), threshold))

    return max(scored)[2]


def summarise_slices(rows: list[dict[str, Any]], predictions: list[str]) -> dict[str, dict[str, float]]:
    golds = [row["gold"] for row in rows]

    summaries = {"all": qa_summary(predictions, golds)}

    for slice_name in SLICES:
        for value in sorted({row[slice_name] for row in rows}):
            positions = [i for i, row in enumerate(rows) if row[slice_name] == value]

            group_predictions = [predictions[i] for i in positions]

            group_golds = [golds[i] for i in positions]

            summaries[f"{slice_name}={value}"] = qa_summary(group_predictions, group_golds)

    return summaries


def out_of_domain_reads(reader: Any, retriever_name: str, passages: list[Passage]) -> list[dict[str, Any]]:
    with open(OUT_OF_DOMAIN_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    passages_by_id = {p["passage_id"]: p for p in passages}

    rankings = retrieve_all(retriever_name, passages, [row["question"] for row in rows])

    ood_rows = []

    for row, top_ids in zip(rows, rankings):
        reads = []

        for passage_id in top_ids:
            answer, margin = read(reader, row["question"], passages_by_id[passage_id]["text"])

            reads.append((answer, margin, passage_id))

        ood_rows.append({"question": row["question"], "distance": row["distance"].strip().lower(), "reads": reads})

    return ood_rows


def refusal_summary(ood_rows: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    refused_by_distance: dict[str, list[float]] = {}

    wrongly_answered = []

    for row in ood_rows:
        answer, passage_id = decide_across_passages(row["reads"], threshold)

        refused_by_distance.setdefault(row["distance"], []).append(1.0 if answer == "" else 0.0)

        if answer:
            wrongly_answered.append({"question": row["question"], "distance": row["distance"], "answer": answer})

    all_refusals = [value for values in refused_by_distance.values() for value in values]

    return {
        "refusal_rate": round(statistics.mean(all_refusals), 3),
        "by_distance": {d: round(statistics.mean(v), 3) for d, v in sorted(refused_by_distance.items())},
        "wrongly_answered": wrongly_answered,
    }


def main() -> None:
    reader_name = sys.argv[1] if len(sys.argv) > 1 else "deepset/roberta-base-squad2"

    retriever_name = sys.argv[2] if len(sys.argv) > 2 else "bm25"

    reader_label = short_name_of(reader_name) + ("" if reader_name.startswith("models/") else " (zero-shot)")

    retriever_label = "BM25"

    if retriever_name != "bm25":
        retriever_label = short_name_of(retriever_name) + ("" if retriever_name.startswith("models/") else " (zero-shot)")

    reader = load_reader(reader_name)

    passages = load_searchable_passages()

    passages_by_id = {p["passage_id"]: p for p in passages}

    rows_by_split: dict[str, list[dict[str, Any]]] = {}

    for split in ["validation", "test"]:
        examples = read_examples(split)

        rankings = retrieve_all(retriever_name, passages, [e["question"] for e in examples])

        rows_by_split[split] = []

        for example, top_ids in zip(examples, rankings):
            retrieved = [passages_by_id[passage_id] for passage_id in top_ids]

            rows_by_split[split].append(raw_reads(reader, example, retrieved))

    threshold = best_threshold(rows_by_split["validation"])

    ood_rows = out_of_domain_reads(reader, retriever_name, passages)

    results: dict[str, Any] = {"reader": reader_name, "retriever": retriever_name, "tuned_threshold": threshold}

    for split, rows in rows_by_split.items():
        gold = gold_predictions(rows, threshold)

        end_to_end = end_to_end_predictions(rows, threshold)

        results[f"{split}/gold_passage"] = summarise_slices(rows, gold)

        results[f"{split}/end_to_end"] = summarise_slices(rows, [answer for answer, _ in end_to_end])

        default_end_to_end = [answer for answer, _ in end_to_end_predictions(rows, 0.0)]

        results[f"{split}/end_to_end_default_threshold"] = summarise_slices(rows, default_end_to_end)

        for row, prediction, (e2e_answer, e2e_passage_id) in zip(rows, gold, end_to_end):
            row["gold_passage_prediction"] = prediction

            row["end_to_end_prediction"] = e2e_answer

            row["end_to_end_passage_id"] = e2e_passage_id

            row["split"] = split

    results["out_of_domain"] = refusal_summary(ood_rows, threshold)

    results["out_of_domain_default_threshold"] = refusal_summary(ood_rows, 0.0)

    record_test_rows(results, rows_by_split["test"], passages_by_id, reader_label, retriever_label, threshold)

    file_stem = f"reader_{short_name_of(reader_name)}_{short_name_of(retriever_name)}"

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    (RESULTS_FOLDER / f"{file_stem}_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    with open(RESULTS_FOLDER / f"{file_stem}_predictions.jsonl", "w", encoding="utf-8") as file:
        for row in rows_by_split["validation"] + rows_by_split["test"]:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    print_summary(results)


def record_test_rows(
    results: dict[str, Any],
    test_rows: list[dict[str, Any]],
    passages_by_id: dict[str, Passage],
    reader_label: str,
    retriever_label: str,
    threshold: float,
) -> None:
    gold = results["test/gold_passage"]["all"]

    end_to_end = results["test/end_to_end"]["all"]

    default = results["test/end_to_end_default_threshold"]["all"]

    answered_ease = [
        passages_by_id[row["end_to_end_passage_id"]]["reading_ease"] for row in test_rows if row["end_to_end_passage_id"]
    ]

    record_experiment(
        {
            "experiment": f"Reader {reader_label}, gold passage",
            "split": "test",
            "questions": gold["questions"],
            "exact_match": gold["exact_match"],
            "f1": gold["f1"],
            "notes": f"threshold {threshold} (tuned on validation); answerable F1 {gold['answerable_f1']}, "
            f"no-answer accuracy {gold['no_answer_accuracy']}",
        }
    )

    end_to_end_row: dict[str, str | float | int] = {
        "experiment": f"{retriever_label} + reader {reader_label}, end to end",
        "split": "test",
        "questions": end_to_end["questions"],
        "exact_match": end_to_end["exact_match"],
        "f1": end_to_end["f1"],
        "ood_refusal_rate": results["out_of_domain"]["refusal_rate"],
        "notes": f"threshold {threshold} (tuned on validation); answerable F1 {end_to_end['answerable_f1']}, "
        f"no-answer accuracy {end_to_end['no_answer_accuracy']}; at threshold 0: F1 {default['f1']}, "
        f"OOD refusal {results['out_of_domain_default_threshold']['refusal_rate']}",
    }

    if answered_ease:
        end_to_end_row["top1_reading_ease"] = round(statistics.mean(answered_ease), 1)

    record_experiment(end_to_end_row)


def print_summary(results: dict[str, Any]) -> None:
    print(f"reader: {results['reader']} | retriever: {results['retriever']} | tuned threshold: {results['tuned_threshold']}")

    print(f"{'setting / slice':52} {'n':>4} {'EM':>6} {'F1':>6} {'ans F1':>7} {'no-ans acc':>10}")

    for key, slices in results.items():
        if "/" not in key:
            continue

        for name, s in slices.items():
            print(
                f"{key + ' / ' + name:52} {s['questions']:>4.0f} {s['exact_match']:>6} {s['f1']:>6}"
                f" {s['answerable_f1']:>7} {s['no_answer_accuracy']:>10}"
            )

    for key in ["out_of_domain", "out_of_domain_default_threshold"]:
        print(f"{key}: refusal {results[key]['refusal_rate']} | by distance {results[key]['by_distance']}")


if __name__ == "__main__":
    main()
