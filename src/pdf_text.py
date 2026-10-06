"""
Read the text lines and table rows out of a PDF.

Lines that are only layout are dropped: table of contents pages, page numbers,
and headers or footers printed on every page.
"""

import re
from collections import Counter
from pathlib import Path

import pdfplumber

PAGE_NUMBER = re.compile(r"^\d{1,3}$")

DOT_LEADER = re.compile(r"(\.\s?){5,}|…{2,}")


def tidy(text: str | None) -> str:
    if text is None:
        return ""

    return " ".join(text.split())


def join_lines(lines: list[str]) -> str:
    """Join lines into one paragraph, so 'self-' plus 'employed' becomes 'self-employed'."""
    text = ""

    for line in lines:
        if text.endswith("-"):
            text = text + line

        elif text:
            text = text + " " + line

        else:
            text = line

    return text


def clean_table_rows(raw_rows: list[list[str | None]]) -> list[list[str]]:
    """A row with an empty first cell is the second line of the row above, so join them."""
    rows: list[list[str]] = []

    for raw_row in raw_rows:
        row = [tidy(cell) for cell in raw_row]

        if not any(row):
            continue

        if row[0] == "" and rows:
            previous = rows[-1]

            for position, cell in enumerate(row):
                previous[position] = (previous[position] + " " + cell).strip()

        else:
            rows.append(row)

    return rows


def trim_to_page(
    box: tuple[float, float, float, float], page_box: tuple[float, float, float, float]
) -> tuple[float, float, float, float]:
    """Some table boxes stick out past the edge of the page, which pdfplumber refuses."""
    left = max(box[0], page_box[0])

    top = max(box[1], page_box[1])

    right = min(box[2], page_box[2])

    bottom = min(box[3], page_box[3])

    return left, top, right, bottom


def is_contents_page(lines: list[str]) -> bool:
    if not lines:
        return False

    dotted_lines = [line for line in lines if DOT_LEADER.search(line)]

    return len(dotted_lines) / len(lines) >= 0.25


def remove_layout_lines(pages: list[list[str]]) -> list[str]:
    """Drop contents pages, page numbers, and lines printed on 30% or more of the pages."""
    pages = [lines for lines in pages if not is_contents_page(lines)]

    pages_with_line: Counter[str] = Counter()

    for lines in pages:
        pages_with_line.update(set(lines))

    repeated_lines: set[str] = set()

    if len(pages) >= 4:
        for line, count in pages_with_line.items():
            if count / len(pages) >= 0.3:
                repeated_lines.add(line)

    kept_lines: list[str] = []

    for lines in pages:
        for line in lines:
            if (
                line in repeated_lines
                or PAGE_NUMBER.match(line)
                or DOT_LEADER.search(line)
            ):
                continue

            kept_lines.append(line)

    return kept_lines


def read_pdf(path: Path) -> tuple[list[str], list[list[str]]]:
    """Return the clean text lines of a PDF, and the rows of every table in it."""
    pages: list[list[str]] = []

    table_rows: list[list[str]] = []

    pdf = pdfplumber.open(path)

    for page in pdf.pages:
        text_area = page

        for table in page.find_tables():
            table_rows += clean_table_rows(table.extract())

            text_area = text_area.outside_bbox(trim_to_page(table.bbox, page.bbox))

        text = text_area.extract_text() or ""

        lines = [tidy(line) for line in text.split("\n")]

        pages.append([line for line in lines if line])

    pdf.close()

    return remove_layout_lines(pages), table_rows
