"""
Split regulations, guidelines and frameworks into passages.

These documents number their clauses like 1.6 and 1.6.1. Each numbered clause becomes
one passage. A short clause with no full stop is a heading, so it is used as the
section name instead. Rows of the definitions tables become "Term: definition" passages.
"""

import re

from src.data_types import DraftPassage
from src.pdf_text import join_lines

MAX_HEADING_WORDS = 15

STARTS_WITH_NUMBER = re.compile(r"^\d{1,3}\b")

CLAUSE_START = re.compile(r"^\d{1,2}(\.\d{1,2}){1,4}\.?\s+[A-Z(]")

FORM_FIELD_WORDS = ("Mandatory", "Non-mandatory", "Non- mandatory", "Conditionally")


def group_into_clauses(lines: list[str]) -> list[str]:
    """Every line that starts with a clause number begins a new clause."""
    clauses: list[str] = []

    current: list[str] = []

    for line in lines:
        if CLAUSE_START.match(line) and current:
            clauses.append(join_lines(current))

            current = []

        current.append(line)

    if current:
        clauses.append(join_lines(current))

    return clauses


def is_heading(clause: str) -> bool:
    return len(clause.split()) < MAX_HEADING_WORDS and not clause.endswith(".")


def definition_from_row(row: list[str]) -> str | None:
    """Read a row as: number, term, definition. Some tables repeat a cell, so repeats are skipped."""
    cells: list[str] = []

    for cell in row:
        if cell and (not cells or cells[-1] != cell):
            cells.append(cell)

    if len(cells) < 3 or not STARTS_WITH_NUMBER.match(cells[0]):
        return None

    term = cells[1]

    meaning = " ".join(cells[2:])

    if len(term.split()) > 8 or len(meaning.split()) < 5:
        return None

    if meaning.startswith(FORM_FIELD_WORDS):
        return None

    return f"{term}: {meaning}"


def parse_legal_document(
    lines: list[str], table_rows: list[list[str]]
) -> list[DraftPassage]:
    passages: list[DraftPassage] = []

    section = "Introduction"

    for clause in group_into_clauses(lines):
        if is_heading(clause):
            section = clause
        else:
            passages.append(
                {
                    "text": clause,
                    "kind": "clause",
                    "section": section,
                    "faq_question": None,
                }
            )

    for row in table_rows:
        definition = definition_from_row(row)

        if definition:
            passages.append(
                {
                    "text": definition,
                    "kind": "definition",
                    "faq_question": None,
                    "section": "Definitions",
                }
            )

    return passages
