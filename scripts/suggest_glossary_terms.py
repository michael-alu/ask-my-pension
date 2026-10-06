"""
Count which acronyms (like RSA) and capitalised phrases (like Retirement Savings Account)
appear in the most passages, to help choose glossary terms.

This only suggests terms. The simple explanations in data/glossary/glossary.csv are
written by hand.

Run from the project root, after build_passages.py:
    python scripts/suggest_glossary_terms.py
"""

import csv
import json
import re
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"

CANDIDATES_FILE = PROJECT_ROOT / "data" / "glossary" / "term_candidates.csv"

GLOSSARY_FILE = PROJECT_ROOT / "data" / "glossary" / "glossary.csv"

ACRONYM = re.compile(r"\b[A-Z][A-Z0-9]{1,6}\b")

PHRASE = re.compile(r"\b[A-Z][a-z]+(?: (?:of |and )?[A-Z][a-z]+){1,3}\b")

NOT_TERMS = {
    "II",
    "III",
    "IV",
    "VI",
    "THE",
    "AND",
    "OF",
    "FOR",
    "TO",
    "IN",
    "OR",
    "NO",
    "PART",
}

TOP_N = 60


def top_terms(counter: Counter[str]) -> list[tuple[str, int]]:
    """Most common first. Ties are sorted alphabetically so the file is the same on every run."""
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))

    return ranked[:TOP_N]


def main() -> None:
    with open(PASSAGES_FILE, encoding="utf-8") as file:
        texts = [json.loads(line)["text"] for line in file]

    acronyms: Counter[str] = Counter()

    phrases: Counter[str] = Counter()

    for text in texts:
        acronyms.update(set(ACRONYM.findall(text)) - NOT_TERMS)

        phrases.update(set(PHRASE.findall(text)))

    CANDIDATES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(CANDIDATES_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(["term", "kind", "passages_containing"])

        for term, count in top_terms(acronyms):
            writer.writerow([term, "acronym", count])

        for term, count in top_terms(phrases):
            writer.writerow([term, "phrase", count])

    if not GLOSSARY_FILE.exists():
        with open(GLOSSARY_FILE, "w", newline="", encoding="utf-8") as file:
            csv.writer(file).writerow(["term", "simple_explanation", "source"])

    print(f"wrote {CANDIDATES_FILE.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
