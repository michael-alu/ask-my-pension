"""
Put every section into train, validation or test, once, before annotating.

Sections are shuffled with a fixed seed, then handed out in order: train until it holds
65% of the passages, validation until 80%, and test gets the rest. Plain and legal
sources are done separately, so both appear in every split.

Do not rerun this after annotating starts, or questions could move between splits.

Run from the project root, after build_passages.py:
    python scripts/make_splits.py
"""

import json
import random
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import Passage  # noqa: E402
from src.splits import SPLITS_FILE, section_key  # noqa: E402

SEED = 13

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"


def read_passages() -> list[Passage]:
    with open(PASSAGES_FILE, encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def split_for_position(share_done: float) -> str:
    if share_done < 0.65:
        return "train"

    if share_done < 0.80:
        return "validation"

    return "test"


def main() -> None:
    if SPLITS_FILE.exists():
        return print(
            f"{SPLITS_FILE.name} already exists, so the splits are frozen. Delete it first to redo them."
        )

    passages = read_passages()

    splits: dict[str, str] = {}

    for style in ["plain", "legal"]:
        section_sizes = Counter(section_key(p) for p in passages if p["style"] == style)

        sections = sorted(section_sizes)

        random.Random(SEED).shuffle(sections)

        done = 0

        total = sum(section_sizes.values())

        counts = {"train": 0, "validation": 0, "test": 0}

        for section in sections:
            split = split_for_position(done / total)

            splits[section] = split

            counts[split] += section_sizes[section]

            done += section_sizes[section]

        print(f"{style}: {counts}")

    SPLITS_FILE.parent.mkdir(parents=True, exist_ok=True)

    file = open(SPLITS_FILE, "w", encoding="utf-8")

    json.dump(splits, file, indent=2, ensure_ascii=False, sort_keys=True)

    file.close()

    print(f"saved {len(splits)} sections to {SPLITS_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
