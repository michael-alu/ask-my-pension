"""
Load the passages the system is allowed to search: every passage except the excluded ones.
"""

import json
from pathlib import Path

from src.data_types import Passage
from src.review_files import load_excluded_ids

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"


def load_searchable_passages() -> list[Passage]:
    excluded_ids = load_excluded_ids()

    with open(PASSAGES_FILE, encoding="utf-8") as file:
        passages: list[Passage] = [json.loads(line) for line in file]

    return [p for p in passages if p["passage_id"] not in excluded_ids]
