"""Small checks run on every passage.

- find_changing_numbers: rates and money amounts, which go out of date. We only
want facts that stay true over time, so these passages are flagged for review.
- reading_ease: Flesch Reading Ease. Higher means easier. Roughly, 60 to 70 is
plain English, and below 30 is very hard, typical of legal text.
"""

import re

from textstat import textstat

PERCENTAGE = re.compile(r"\d+(?:\.\d+)?\s?(?:%|per\s?cent\b|percent\b)", re.IGNORECASE)

NAIRA_WORD_AMOUNT = re.compile(
    r"\d[\d,]*(?:\.\d+)?\s?(?:million\s|billion\s)?naira\b", re.IGNORECASE
)

NAIRA_SYMBOL_AMOUNT = re.compile(
    r"(?:₦|\bN|\bNGN\s?)\d[\d,]*(?:\.\d+)?(?:\s?(?:million|billion|thousand))?"
)


def find_changing_numbers(text: str) -> list[str]:
    found: list[str] = []

    for pattern in [PERCENTAGE, NAIRA_SYMBOL_AMOUNT, NAIRA_WORD_AMOUNT]:
        for match in pattern.finditer(text):
            found.append(match.group(0).strip())

    return sorted(set(found))


def reading_ease(text: str) -> float:
    score: float = textstat.flesch_reading_ease(text)

    return round(score, 1)
