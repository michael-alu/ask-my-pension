"""
Sort every test question into one outcome type, so we can see how and why the system fails.

Each answerable question gets exactly one type, checked in this order:
- "correct": F1 of at least 0.8 against the gold answer
- "refused but answerable": the system gave no answer
- "retriever missed the gold passage": answered from another passage, with F1 below 0.5, and the
  gold passage was not among the 3 passages read
- "gold passage read, answer taken from another": the gold passage was among the 3 read, but the
  reader was more confident in an answer from a different passage, with F1 below 0.5
- "right passage, wrong span": answered from the gold passage, with F1 below 0.5
- "partly right, too long" / "too short" / "partial overlap": F1 from 0.5 to 0.8, split by how the
  answer's length compares with the gold answer's
Each no-answer question is "correctly refused" or "answered but should have refused".
Out-of-domain questions are "correctly refused" or "answered an out-of-domain question".

Correct answers whose passage has a Flesch Reading Ease below 30 (very hard) are also counted as
"correct but hard to read", because a right answer a worker cannot understand still fails them.

Automatic scoring assumes each question has one right passage, but the documents overlap: an
answer from a different document can be just as correct. So the cases most likely to hide correct
answers ("gold passage read, answer taken from another" and "answered but should have refused") are
written to results/manual_review.csv for a human to mark "yes", "partly" or "no". The file is never
overwritten, and once it is filled in, the corrected accuracy is reported next to the automatic one.

Writes results/error_analysis.json and results/error_analysis.md, with counts by slice and examples.

Run from the project root:
    python scripts/error_analysis.py <predictions file of the system to analyse>
"""

import csv
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.passages import load_searchable_passages  # noqa: E402
from src.qa_metrics import f1  # noqa: E402

RESULTS_FOLDER = PROJECT_ROOT / "results"

SQUAD_TEST_FILE = PROJECT_ROOT / "data" / "squad" / "test.jsonl"

DEFAULT_SYSTEM = "reader_reader-roberta-base-squad2-100pct-matched_retriever-bge-small-en-v1.5-100pct"

HARD_TO_READ = 30.0

EXAMPLES_PER_TYPE = 4

REVIEW_FILE = RESULTS_FOLDER / "manual_review.csv"

REVIEW_OUTCOMES = ["gold passage read, answer taken from another", "answered but should have refused"]


def outcome_of(row: dict[str, Any], gold_passage_id: str) -> str:
    prediction = row["end_to_end_prediction"]

    gold = row["gold"]

    if gold is None:
        return "correctly refused" if prediction == "" else "answered but should have refused"

    if prediction == "":
        return "refused but answerable"

    score = f1(prediction, gold)

    if score >= 0.8:
        return "correct"

    if score < 0.5:
        passages_read = [passage_id for _, _, passage_id in row["end_to_end_reads"]]

        if row["end_to_end_passage_id"] == gold_passage_id:
            return "right passage, wrong span"

        if gold_passage_id in passages_read:
            return "gold passage read, answer taken from another"

        return "retriever missed the gold passage"

    length_ratio = len(prediction.split()) / max(len(gold.split()), 1)

    if length_ratio > 1.5:
        return "partly right, too long"

    if length_ratio < 0.67:
        return "partly right, too short"

    return "partly right, partial overlap"


def main() -> None:
    system = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SYSTEM

    with open(RESULTS_FOLDER / f"{system}_predictions.jsonl", encoding="utf-8") as file:
        rows = [json.loads(line) for line in file if '"split": "test"' in line]

    with open(SQUAD_TEST_FILE, encoding="utf-8") as file:
        gold_passage_of = {json.loads(line)["id"]: json.loads(line)["passage_id"] for line in file}

    reading_ease = {p["passage_id"]: p["reading_ease"] for p in load_searchable_passages()}

    system_results = json.loads((RESULTS_FOLDER / f"{system}_results.json").read_text(encoding="utf-8"))

    analysed = []

    for row in rows:
        outcome = outcome_of(row, gold_passage_of[row["id"]])

        answer_passage = row["end_to_end_passage_id"]

        hard_to_read = outcome == "correct" and answer_passage is not None and reading_ease[answer_passage] < HARD_TO_READ

        analysed.append({**row, "outcome": outcome, "hard_to_read": hard_to_read})

    counts = dict(Counter(row["outcome"] for row in analysed).most_common())

    by_slice: dict[str, dict[str, int]] = {}

    for slice_name in ["origin", "style", "level"]:
        for value in sorted({row[slice_name] for row in analysed}):
            group = [row for row in analysed if row[slice_name] == value]

            by_slice[f"{slice_name}={value}"] = dict(Counter(row["outcome"] for row in group).most_common())

    examples: dict[str, list[dict[str, Any]]] = {}

    for outcome in counts:
        chosen = [row for row in analysed if row["outcome"] == outcome][:EXAMPLES_PER_TYPE]

        examples[outcome] = [
            {
                "question": row["question"],
                "gold": row["gold"],
                "prediction": row["end_to_end_prediction"],
                "origin": row["origin"],
                "style": row["style"],
            }
            for row in chosen
        ]

    out_of_domain = system_results["out_of_domain"]

    write_review_sheet_if_missing(analysed)

    summary = {
        "system": system,
        "test_questions": len(analysed),
        "counts": counts,
        "correct_but_hard_to_read": sum(1 for row in analysed if row["hard_to_read"]),
        "by_slice": by_slice,
        "out_of_domain_refusal_rate": out_of_domain["refusal_rate"],
        "out_of_domain_by_distance": out_of_domain["by_distance"],
        "out_of_domain_answered": out_of_domain["wrongly_answered"],
        "examples": examples,
        "manual_review": review_summary(counts.get("correct", 0)),
    }

    (RESULTS_FOLDER / "error_analysis.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    (RESULTS_FOLDER / "error_analysis.md").write_text(as_markdown(summary), encoding="utf-8")

    print(as_markdown(summary))


def write_review_sheet_if_missing(analysed: list[dict[str, Any]]) -> None:
    if REVIEW_FILE.exists():
        return

    with open(REVIEW_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["id", "outcome", "question", "gold_answer", "system_answer", "system_passage_id", "acceptable"])

        for row in analysed:
            if row["outcome"] in REVIEW_OUTCOMES:
                gold = row["gold"] or "(no answer in its own passage)"

                writer.writerow(
                    [row["id"], row["outcome"], row["question"], gold, row["end_to_end_prediction"], row["end_to_end_passage_id"], ""]
                )

    print(f"wrote {REVIEW_FILE.relative_to(PROJECT_ROOT)} for a human to mark yes, partly or no")


def review_summary(automatic_correct: int) -> dict[str, int]:
    """Counts of the human labels, and the number correct once the "yes" answers are added."""
    if not REVIEW_FILE.exists():
        return {}

    with open(REVIEW_FILE, newline="", encoding="utf-8") as file:
        labels = [row["acceptable"].strip().lower() for row in csv.DictReader(file)]

    return {
        "reviewed": sum(1 for label in labels if label),
        "yes": labels.count("yes"),
        "partly": labels.count("partly"),
        "no": labels.count("no"),
        "correct_after_review": automatic_correct + labels.count("yes"),
    }


def short(text: str | None, limit: int = 140) -> str:
    if text is None:
        return "(no answer)"

    if text == "":
        return "(refused)"

    text = " ".join(text.split())

    return text if len(text) <= limit else text[:limit] + "..."


def as_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Error analysis",
        "",
        f"System: `{summary['system']}`, {summary['test_questions']} test questions.",
        "",
        "## Outcomes",
        "",
        "| Outcome | Count |",
        "|---|---|",
    ]

    for outcome, count in summary["counts"].items():
        lines.append(f"| {outcome} | {count} |")

    lines += [
        "",
        f"Correct but hard to read (answer passage Flesch Reading Ease below {HARD_TO_READ:.0f}): "
        f"{summary['correct_but_hard_to_read']}",
        "",
        "## Outcomes by slice",
        "",
    ]

    for slice_name, slice_counts in summary["by_slice"].items():
        parts = ", ".join(f"{outcome}: {count}" for outcome, count in slice_counts.items())

        lines.append(f"- **{slice_name}**: {parts}")

    lines += [
        "",
        "## Out of domain",
        "",
        f"Refusal rate {summary['out_of_domain_refusal_rate']}, by distance {summary['out_of_domain_by_distance']}.",
        "",
    ]

    for item in summary["out_of_domain_answered"]:
        lines.append(f"- [{item['distance']}] {item['question']} -> \"{short(item['answer'])}\"")

    review = summary["manual_review"]

    if review.get("reviewed"):
        lines += [
            "",
            "## Human review",
            "",
            f"{review['reviewed']} answers taken from another passage were checked by hand: {review['yes']} acceptable, "
            f"{review['partly']} partly, {review['no']} not. Correct answers: {summary['counts'].get('correct', 0)} by the "
            f"automatic score, {review['correct_after_review']} after review, out of {summary['test_questions']}.",
        ]

    lines += ["", "## Examples", ""]

    for outcome, items in summary["examples"].items():
        lines.append(f"### {outcome}")
        lines.append("")

        for item in items:
            lines.append(f"- **Q** ({item['origin']}, {item['style']}): {item['question']}")
            lines.append(f"  - gold: {short(item['gold'])}")
            lines.append(f"  - system: {short(item['prediction'])}")

        lines.append("")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
