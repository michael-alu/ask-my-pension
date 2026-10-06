"""
Which split (train, validation or test) each passage belongs to.

Passages are split by section, never one by one. Questions about the same section share
wording and facts, so if some were in training and others in test, the model could pass
the test by remembering instead of understanding.
"""

import json
from pathlib import Path

from src.data_types import Passage

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SPLITS_FILE = PROJECT_ROOT / "data" / "splits" / "sections.json"


def section_key(passage: Passage) -> str:
    return f"{passage['source_id']}::{passage['section']}"


def load_splits() -> dict[str, str]:
    file = open(SPLITS_FILE, encoding="utf-8")

    splits: dict[str, str] = json.load(file)

    file.close()

    return splits


def split_of(passage: Passage, splits: dict[str, str]) -> str:
    return splits.get(section_key(passage), "unassigned")
