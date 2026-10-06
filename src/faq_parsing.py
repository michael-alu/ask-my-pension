"""
Turn FAQ documents into passages, keeping the original wording.

Each answer becomes one passage, with its question kept next to it. Text that sits
under a section heading before any question (like a list of steps) becomes a
passage with no question, called a note.
"""

import re

from bs4 import BeautifulSoup, Tag

from src.data_types import DraftPassage
from src.pdf_text import join_lines, tidy

MIN_NOTE_WORDS = 15

PART_HEADING = re.compile(r"^PART\s+\d+$")

QUESTION_START = re.compile(r"^\d{1,3}\.\s+")

SECTION_HEADING = re.compile(r"^[A-Z]\.\s+[A-Z][A-Z0-9 ,&()/'’\-]+$")


def make_passage(section: str, question: str | None, answer: str) -> DraftPassage:
    if question is None:
        return {
            "text": answer,
            "kind": "faq_note",
            "section": section,
            "faq_question": None,
        }

    return {
        "text": answer,
        "section": section,
        "kind": "faq_answer",
        "faq_question": question,
    }


def save_answer(
    passages: list[DraftPassage],
    section: str,
    question: str | None,
    answer_lines: list[str],
) -> None:
    answer = join_lines(answer_lines)

    is_short_note = question is None and len(answer.split()) < MIN_NOTE_WORDS

    if answer and not is_short_note:
        passages.append(make_passage(section, question, answer))


def read_question(lines: list[str], index: int) -> tuple[str | None, int]:
    """A question is a numbered line that ends with '?' within 4 lines. This function returns it and the lines used."""
    if not QUESTION_START.match(lines[index]):
        return None, 0

    question_lines = lines[index : index + 4]

    for count, line in enumerate(question_lines, start=1):
        if line.endswith("?"):
            question = join_lines(question_lines[:count])

            return QUESTION_START.sub("", question), count

    return None, 0


def parse_pdf_faq(lines: list[str], first_section: str) -> list[DraftPassage]:
    index = 0

    section = first_section

    question: str | None = None

    answer_lines: list[str] = []

    passages: list[DraftPassage] = []

    while index < len(lines):
        line = lines[index]

        if line.lower() == "enquiries":
            break

        if PART_HEADING.match(line):
            index += 1

            continue

        if SECTION_HEADING.match(line):
            save_answer(passages, section, question, answer_lines)

            section = line

            question = None

            answer_lines = []

            index += 1

            continue

        new_question, lines_used = read_question(lines, index)

        if new_question:
            save_answer(passages, section, question, answer_lines)

            question = new_question

            answer_lines = []

            index += lines_used

            continue

        answer_lines.append(line)

        index += 1

    save_answer(passages, section, question, answer_lines)

    return passages


def parse_trustfund_faq(html: bytes) -> list[DraftPassage]:
    """Questions are in bold, everything after a question, up to the next one, is its answer."""

    soup = BeautifulSoup(html, "html.parser")

    passages: list[DraftPassage] = []

    for item in soup.select("div.elementor-accordion-item"):
        title = item.select_one(".elementor-tab-title")

        content = item.select_one(".elementor-tab-content")

        if title is None or content is None:
            continue

        section = re.sub(r"^\d+\s*", "", tidy(title.get_text(" ")))

        question: str | None = None

        answer_parts: list[str] = []

        for element in content.find_all(recursive=False):
            if not isinstance(element, Tag):
                continue

            text = tidy(element.get_text(" "))

            bold = element.find("strong")

            is_question = (
                bold is not None
                and tidy(bold.get_text(" ")) == text
                and text.endswith("?")
            )

            if is_question:
                save_answer(passages, section, question, answer_parts)

                question = text

                answer_parts = []

            elif text and question:
                answer_parts.append(text)

        save_answer(passages, section, question, answer_parts)

    return passages


def parse_fcmb_faq(html: bytes) -> list[DraftPassage]:
    """Each question is a button, and its answer sits in the card body under it."""
    soup = BeautifulSoup(html, "html.parser")

    passages: list[DraftPassage] = []

    for card in soup.select("div.card.accordion-item"):
        button = card.select_one("button.accordion-button")

        body = card.select_one("div.card-body")

        if button is None or body is None:
            continue

        question = re.sub(r"^Q\d+\.\s*", "", tidy(button.get_text(" ")))

        answer = re.sub(r"^A\d+\.\s*", "", tidy(body.get_text(" ")))

        passages.append(make_passage("FAQs", question, answer))

    return passages
