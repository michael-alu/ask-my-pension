"""
The glossary: pension terms with a simple explanation, written by hand in data/glossary/glossary.csv.

When an answer or its passage contains a glossary term, the app shows the explanation under the answer.
Terms are matched as whole words, ignoring case, so "PFA" matches "pfa" but not "PFAs" inside "PFAS".
"""

import csv
import re
from pathlib import Path
from typing import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GLOSSARY_FILE = PROJECT_ROOT / "data" / "glossary" / "glossary.csv"


class GlossaryEntry(TypedDict):
    term: str
    explanation: str
    source: str


def load_glossary() -> list[GlossaryEntry]:
    if not GLOSSARY_FILE.exists():
        return []

    with open(GLOSSARY_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    entries: list[GlossaryEntry] = []

    for row in rows:
        term = (row.get("term") or "").strip()

        explanation = (row.get("simple_explanation") or "").strip()

        source = (row.get("source_note") or row.get("source") or row.get("source_id") or "").strip()

        if term and explanation:
            entries.append({"term": term, "explanation": explanation, "source": source})

    return entries


def terms_in(text: str, glossary: list[GlossaryEntry]) -> list[GlossaryEntry]:
    """The glossary entries whose term appears in the text, in glossary order."""
    found: list[GlossaryEntry] = []

    for entry in glossary:
        pattern = r"\b" + re.escape(entry["term"]) + r"s?\b"

        if re.search(pattern, text, flags=re.IGNORECASE):
            found.append(entry)

    return found
