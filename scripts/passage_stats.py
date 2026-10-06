"""
Count the passages and compare how easy plain and legal sources are to read.

Run from the project root, after build_passages.py:
    python scripts/passage_stats.py
"""

import json
import statistics
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

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
