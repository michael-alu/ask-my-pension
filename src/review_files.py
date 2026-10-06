"""
Hand-edited files that keep some passages out of search.

- excluded_passages.csv: passages kept out, with a reason
- number_review.csv: passages with rates or naira amounts; "drop" in the decision column keeps them out
"""

import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ANNOTATIONS_FOLDER = PROJECT_ROOT / "data" / "annotations"

EXCLUDED_FILE = ANNOTATIONS_FOLDER / "excluded_passages.csv"

NUMBER_REVIEW_FILE = ANNOTATIONS_FOLDER / "number_review.csv"

OUT_OF_DOMAIN_FILE = ANNOTATIONS_FOLDER / "out_of_domain.csv"


def read_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with open(path, newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_excluded_ids() -> set[str]:
    excluded = {row["passage_id"] for row in read_rows(EXCLUDED_FILE)}

    for row in read_rows(NUMBER_REVIEW_FILE):
        if row["decision"].strip().lower() == "drop":
            excluded.add(row["passage_id"])

    return excluded
