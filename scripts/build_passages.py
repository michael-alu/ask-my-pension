"""
Clean the raw documents and split them into passages.

Reads every core source in data/sources.csv from data/raw/ and writes one passage per
line to data/processed/passages.jsonl.

Run from the project root:
    python scripts/build_passages.py
"""

import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import DraftPassage, Passage  # noqa: E402
from src.faq_parsing import (
    parse_fcmb_faq,
    parse_pdf_faq,
    parse_trustfund_faq,
)  # noqa: E402
from src.legal_parsing import parse_legal_document  # noqa: E402
from src.passage_checks import find_changing_numbers, reading_ease  # noqa: E402
from src.pdf_text import read_pdf  # noqa: E402

RAW_FOLDER = PROJECT_ROOT / "data" / "raw"

SOURCES_FILE = PROJECT_ROOT / "data" / "sources.csv"

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"


def read_core_sources() -> list[dict[str, str]]:
    file = open(SOURCES_FILE, newline="", encoding="utf-8")

    sources = list(csv.DictReader(file))

    file.close()

    return [source for source in sources if source["in_core"] == "yes"]


def draft_passages_for(source: dict[str, str]) -> list[DraftPassage]:
    source_id = source["source_id"]

    path = RAW_FOLDER / f"{source_id}.{source['file_type']}"

    if source_id == "trustfund_faq":
        return parse_trustfund_faq(path.read_bytes())

    if source_id == "fcmb_faq":
        return parse_fcmb_faq(path.read_bytes())

    lines, table_rows = read_pdf(path)

    if source["style"] == "plain":
        return parse_pdf_faq(lines, source["title"])

    return parse_legal_document(lines, table_rows)


def finish_passage(draft: DraftPassage, source: dict[str, str], number: int) -> Passage:
    return {
        "kind": draft["kind"],
        "text": draft["text"],
        "style": source["style"],
        "section": draft["section"],
        "source_id": source["source_id"],
        "faq_question": draft["faq_question"],
        "reading_ease": reading_ease(draft["text"]),
        "passage_id": f"{source['source_id']}-{number:04d}",
        "changing_numbers": find_changing_numbers(draft["text"]),
    }


def main() -> None:
    passages: list[Passage] = []

    for source in read_core_sources():
        drafts = draft_passages_for(source)

        for number, draft in enumerate(drafts, start=1):
            passages.append(finish_passage(draft, source, number))

        print(f"{source['source_id']:36} {len(drafts):>4} passages")

    PASSAGES_FILE.parent.mkdir(parents=True, exist_ok=True)

    file = open(PASSAGES_FILE, "w", encoding="utf-8")

    for passage in passages:
        file.write(json.dumps(passage, ensure_ascii=False) + "\n")

    file.close()

    print(f"{'TOTAL':36} {len(passages):>4} passages")


if __name__ == "__main__":
    main()
