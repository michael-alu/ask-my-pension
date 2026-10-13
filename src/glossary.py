"""
The glossary: pension terms with a simple explanation, written by hand in data/glossary/glossary.csv.

When an answer or its passage contains a glossary term, the app shows the explanation under the answer.

A term can be written with its full name in brackets, like "RSA (Retirement Savings Account)". The
app then shows that full name, and matches either form in the text: "RSA" or "Retirement Savings
Account". Matching ignores capitals and allows a plural "s", but only matches whole words.

The source_id column holds the passage ids the explanation was written from. The app turns those
into document names. The source_note column is the author's private working notes and is not shown.
"""

import csv
import re
from pathlib import Path
from typing import TypedDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GLOSSARY_FILE = PROJECT_ROOT / "data" / "glossary" / "glossary.csv"

SOURCES_FILE = PROJECT_ROOT / "data" / "sources.csv"


class GlossaryEntry(TypedDict):
    term: str
    explanation: str
    source: str
    match_forms: list[str]


def forms_of(term: str) -> list[str]:
    """ "RSA (Retirement Savings Account)" gives ["RSA", "Retirement Savings Account"]. """
    if "(" not in term:
        return [term]

    short_form = term.split("(")[0].strip()

    long_form = term.split("(")[1].rstrip(")").strip()

    return [short_form, long_form]


def document_names(source_ids: str, titles: dict[str, str]) -> str:
    """ "pencom_faq_2023-0006;fcmb_faq-0008" gives the two document titles, without repeats. """
    names: list[str] = []

    for passage_id in source_ids.split(";"):
        source_id = passage_id.strip().rsplit("-", 1)[0]

        title = titles.get(source_id)

        if title and title not in names:
            names.append(title)

    return "; ".join(names)


def load_titles() -> dict[str, str]:
    """Each document's title with its publisher, because some titles are just "FAQs"."""
    with open(SOURCES_FILE, newline="", encoding="utf-8") as file:
        return {row["source_id"]: f"{row['title']} ({row['publisher']})" for row in csv.DictReader(file)}


def load_glossary() -> list[GlossaryEntry]:
    if not GLOSSARY_FILE.exists():
        return []

    with open(GLOSSARY_FILE, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    titles = load_titles()

    entries: list[GlossaryEntry] = []

    for row in rows:
        term = (row.get("term") or "").strip()

        explanation = (row.get("simple_explanation") or "").strip()

        if not term or not explanation:
            continue

        entries.append(
            {
                "term": term,
                "explanation": explanation,
                "source": document_names(row.get("source_id") or "", titles),
                "match_forms": forms_of(term),
            }
        )

    return entries


def terms_in(text: str, glossary: list[GlossaryEntry]) -> list[GlossaryEntry]:
    """The glossary entries with any form of their term in the text, in glossary order."""
    found: list[GlossaryEntry] = []

    for entry in glossary:
        for form in entry["match_forms"]:
            pattern = r"\b" + re.escape(form) + r"s?\b"

            if re.search(pattern, text, flags=re.IGNORECASE):
                found.append(entry)

                break

    return found
