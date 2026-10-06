"""
The shapes of the records passed around this project.

These work like TypeScript interfaces. A TypedDict is a plain dict when the code runs,
but mypy checks its keys and value types.
"""

from typing import Literal, TypedDict

Kind = Literal["faq_answer", "faq_note", "clause", "definition"]


class DraftPassage(TypedDict):
    kind: Kind
    section: str
    faq_question: str | None
    text: str


class Passage(TypedDict):
    passage_id: str
    source_id: str
    style: str
    kind: Kind
    section: str
    faq_question: str | None
    text: str
    reading_ease: float
    changing_numbers: list[str]


class Annotation(TypedDict):
    annotation_id: str
    question: str
    passage_id: str
    answer_text: str | None
    answer_start: int | None
    level: str
    from_faq: bool
