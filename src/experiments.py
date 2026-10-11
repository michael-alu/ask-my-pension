"""
One table of every experiment, saved as results/experiments.csv and results/experiments.md.

Running the same experiment on the same split again replaces its old row, so the table
always shows the latest result for each.
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXPERIMENTS_CSV = PROJECT_ROOT / "results" / "experiments.csv"

EXPERIMENTS_MD = PROJECT_ROOT / "results" / "experiments.md"

COLUMNS = [
    "experiment",
    "split",
    "questions",
    "recall_at_1",
    "recall_at_5",
    "mrr_at_10",
    "exact_match",
    "f1",
    "ood_refusal_rate",
    "top1_reading_ease",
    "notes",
]


def read_rows() -> list[dict[str, str]]:
    if not EXPERIMENTS_CSV.exists():
        return []

    with open(EXPERIMENTS_CSV, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def write_markdown(rows: list[dict[str, str]]) -> None:
    lines = ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]

    for row in rows:
        lines.append("| " + " | ".join(row[column] for column in COLUMNS) + " |")

    EXPERIMENTS_MD.write_text("# Experiments\n\n" + "\n".join(lines) + "\n", encoding="utf-8")


def record_experiment(row: dict[str, str | float | int]) -> None:
    rows = read_rows()

    rows = [r for r in rows if not (r["experiment"] == row["experiment"] and r["split"] == row["split"])]

    rows.append({column: str(row.get(column, "")) for column in COLUMNS})

    EXPERIMENTS_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(EXPERIMENTS_CSV, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    write_markdown(rows)
