"""
Count the passages and compare how easy plain and legal sources are to read.

Run from the project root, after build_passages.py:
    python scripts/passage_stats.py
"""

import json
import statistics
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.passage_checks import grade_level  # noqa: E402

STATS_FILE = PROJECT_ROOT / "results" / "passage_stats.json"

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"


def main() -> None:
    passages_file = open(PASSAGES_FILE, encoding="utf-8")

    passages = [json.loads(line) for line in passages_file]

    passages_file.close()

    stats: dict[str, float] = {"passages": len(passages)}

    for style in ["plain", "legal"]:
        group = [p for p in passages if p["style"] == style]

        scores = [p["reading_ease"] for p in group]

        stats[f"{style}_passages"] = len(group)

        stats[f"{style}_reading_ease_mean"] = round(statistics.mean(scores), 1)

        stats[f"{style}_reading_ease_median"] = round(statistics.median(scores), 1)

        grades = [grade_level(p["text"]) for p in group]

        stats[f"{style}_grade_level_mean"] = round(statistics.mean(grades), 1)

        stats[f"{style}_grade_level_median"] = round(statistics.median(grades), 1)

        stats[f"{style}_with_changing_numbers"] = sum(
            1 for p in group if p["changing_numbers"]
        )

    STATS_FILE.parent.mkdir(parents=True, exist_ok=True)

    stats_file = open(STATS_FILE, "w", encoding="utf-8")

    json.dump(stats, stats_file, indent=2, ensure_ascii=False, sort_keys=True)

    stats_file.close()

    for name, value in stats.items():
        print(f"{name:32} {value}")


if __name__ == "__main__":
    main()
