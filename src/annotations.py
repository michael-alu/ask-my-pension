"""
`annotations.py` reads, writes, and summarizes the handwritten annotations.

Any annotation points to a passage using its id and indicates from where in the passage to extract the answer.
The passage text itself is not stored as it is owned by the publishers.
It is simply re-integrated when exporting in SQuAD format.
"""

import json
from pathlib import Path

from src.data_types import Annotation, Passage
from src.splits import split_of

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ANNOTATIONS_FILE = PROJECT_ROOT / "data" / "annotations" / "annotations.jsonl"


def load_annotations() -> list[Annotation]:
    if not ANNOTATIONS_FILE.exists():
        return []

    file = open(ANNOTATIONS_FILE, encoding="utf-8")

    lines = file.readlines()

    annotations = [json.loads(line) for line in lines if line.strip()]

    file.close()

    return annotations


def save_annotations(annotations: list[Annotation]) -> None:
    """Write to a temporary file first, then swap it in, so a failed write never damages the real file."""
    ANNOTATIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    temporary_file = ANNOTATIONS_FILE.with_suffix(".jsonl.tmp")

    file = open(temporary_file, "w", encoding="utf-8")

    for annotation in annotations:
        file.write(json.dumps(annotation, ensure_ascii=False) + "\n")

    file.close()

    temporary_file.replace(ANNOTATIONS_FILE)


def find_answer_start(passage_text: str, answer: str) -> int | None:
    position = passage_text.find(answer)

    if position == -1:
        return None

    return position


def progress_report(
    annotations: list[Annotation],
    passages_by_id: dict[str, Passage],
    splits: dict[str, str],
) -> str:
    total = len(annotations)

    if total == 0:
        return "No annotations yet."

    beginner = sum(1 for a in annotations if a["level"] == "beginner")

    no_answer = sum(1 for a in annotations if a["answer_text"] is None)

    from_faq = sum(1 for a in annotations if a["from_faq"])

    beginner_share = beginner / total

    per_split = {"train": 0, "validation": 0, "test": 0}

    own_in_test = 0

    plain = 0

    for annotation in annotations:
        passage = passages_by_id[annotation["passage_id"]]

        split = split_of(passage, splits)

        per_split[split] = per_split.get(split, 0) + 1

        if split == "test" and not annotation["from_faq"]:
            own_in_test += 1

        if passage["style"] == "plain":
            plain += 1

    lines = [
        f"**{total} annotations** | from FAQ: {from_faq} | your own: {total - from_faq} | no answer: {no_answer}",
        f"beginner: {beginner} ({beginner_share:.0%}) | detailed: {total - beginner}",
        f"train: {per_split['train']} | validation: {per_split['validation']} | test: {per_split['test']} "
        f"(your own in test: {own_in_test})",
        f"plain passages: {plain} | legal passages: {total - plain}",
    ]

    if total >= 20 and beginner_share < 0.4:
        lines.append(
            "**Warning:** fewer than 40% beginner questions. Beginners are the main users."
        )

    return "  \n".join(lines)
