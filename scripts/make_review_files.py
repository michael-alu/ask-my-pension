"""
Create the hand-edited review files. Files that already exist are never overwritten.

- excluded_passages.csv: starts with the FCMB questions about FCMB itself, so the app never
  looks like it recommends one pension company
- number_review.csv: every passage with a rate or naira amount; write "keep" or "drop"
- out_of_domain.csv: empty, for questions the system should politely refuse
- faq_levels.csv: the test and validation FAQ questions; write "beginner" or "detailed" for each

Run from the project root, after build_passages.py:
    python scripts/make_review_files.py
"""

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import Passage  # noqa: E402
from src.review_files import (  # noqa: E402
    EXCLUDED_FILE,
    FAQ_LEVELS_FILE,
    NUMBER_REVIEW_FILE,
    OUT_OF_DOMAIN_FILE,
)
from src.splits import load_splits, split_of  # noqa: E402

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"


def read_passages() -> list[Passage]:
    file = open(PASSAGES_FILE, encoding="utf-8")

    lines = [json.loads(line) for line in file]

    file.close()

    return lines


def write_if_missing(path: Path, header: list[str], rows: list[list[str]]) -> None:
    if path.exists():
        return print(f"{path.name} already exists, left as it is")

    path.parent.mkdir(parents=True, exist_ok=True)

    file = open(path, "w", newline="", encoding="utf-8")

    writer = csv.writer(file)

    writer.writerow(header)

    writer.writerows(rows)

    file.close()

    print(f"created {path.name} with {len(rows)} rows")


def main() -> None:
    passages = read_passages()

    excluded_rows: list[list[str]] = []

    for passage in passages:
        question = passage["faq_question"] or ""

        if "FCMB" in question:
            excluded_rows.append(
                [passage["passage_id"], f"company specific: {question}"]
            )

    number_rows: list[list[str]] = []

    for passage in passages:
        if passage["changing_numbers"]:
            numbers = ", ".join(passage["changing_numbers"])
            number_rows.append(
                [passage["passage_id"], numbers, "", passage["text"][:140]]
            )

    write_if_missing(EXCLUDED_FILE, ["passage_id", "reason"], excluded_rows)

    write_if_missing(
        NUMBER_REVIEW_FILE,
        ["passage_id", "numbers", "decision", "preview"],
        number_rows,
    )

    write_if_missing(OUT_OF_DOMAIN_FILE, ["question", "distance", "note"], [])

    splits = load_splits()

    excluded_ids = {row[0] for row in excluded_rows}

    level_rows: list[list[str]] = []

    for passage in passages:
        faq_question = passage["faq_question"]

        split = split_of(passage, splits)

        if faq_question is None or passage["passage_id"] in excluded_ids:
            continue

        if split in ("test", "validation"):
            level_rows.append([passage["passage_id"], split, faq_question, ""])

    write_if_missing(FAQ_LEVELS_FILE, ["passage_id", "split", "question", "level"], level_rows)


if __name__ == "__main__":
    main()
