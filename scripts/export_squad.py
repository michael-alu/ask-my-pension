"""
Build the SQuAD 2.0 style files the reader is trained and evaluated on.

Every example is a question, a passage (the context), and the answer span, or no answer.
Examples come from three places, recorded in the "origin" field:
- "faq_rule": an FAQ question, with its whole FAQ answer as the span
- "faq_human": an FAQ question whose span was marked by hand in the annotation tool
- "own": a question written by hand in the annotation tool

Writes data/squad/train.jsonl, validation.jsonl and test.jsonl. These hold passage text,
so they are not committed. Rerun this script to rebuild them.

Run from the project root:
    python scripts/export_squad.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.annotations import load_annotations  # noqa: E402
from src.data_types import Annotation, Passage, SquadExample  # noqa: E402
from src.eval_questions import load_faq_levels  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.splits import load_splits, split_of  # noqa: E402

SQUAD_FOLDER = PROJECT_ROOT / "data" / "squad"

SPLITS = ["train", "validation", "test"]


def faq_example(passage: Passage, question: str, level: str, split: str) -> SquadExample:
    return {
        "id": f"{passage['passage_id']}::faq",
        "question": question,
        "context": passage["text"],
        "answer_text": passage["text"],
        "answer_start": 0,
        "passage_id": passage["passage_id"],
        "origin": "faq_rule",
        "level": level,
        "style": passage["style"],
        "split": split,
    }


def annotation_example(annotation: Annotation, passage: Passage, origin: str, split: str) -> SquadExample:
    return {
        "id": annotation["annotation_id"],
        "question": annotation["question"],
        "context": passage["text"],
        "answer_text": annotation["answer_text"],
        "answer_start": annotation["answer_start"],
        "passage_id": passage["passage_id"],
        "origin": origin,
        "level": annotation["level"],
        "style": passage["style"],
        "split": split,
    }


def main() -> None:
    passages_by_id = {p["passage_id"]: p for p in load_searchable_passages()}

    splits = load_splits()

    annotations = load_annotations()

    faq_levels = load_faq_levels(annotations)

    hand_marked_faq = {a["passage_id"]: a for a in annotations if a["from_faq"]}

    examples: list[SquadExample] = []

    for passage in passages_by_id.values():
        question = passage["faq_question"]

        if question is None:
            continue

        split = split_of(passage, splits)

        human_annotation = hand_marked_faq.get(passage["passage_id"])

        if human_annotation is not None:
            examples.append(annotation_example(human_annotation, passage, "faq_human", split))
        else:
            level = faq_levels.get(passage["passage_id"], "unlabelled")

            examples.append(faq_example(passage, question, level, split))

    for annotation in annotations:
        annotated_passage = passages_by_id.get(annotation["passage_id"])

        if annotation["from_faq"] or annotated_passage is None:
            continue

        examples.append(annotation_example(annotation, annotated_passage, "own", split_of(annotated_passage, splits)))

    SQUAD_FOLDER.mkdir(parents=True, exist_ok=True)

    for split in SPLITS:
        in_split = [e for e in examples if e["split"] == split]

        with open(SQUAD_FOLDER / f"{split}.jsonl", "w", encoding="utf-8") as file:
            for example in in_split:
                file.write(json.dumps(example, ensure_ascii=False) + "\n")

        origins = {origin: sum(1 for e in in_split if e["origin"] == origin) for origin in ["faq_rule", "faq_human", "own"]}

        no_answer = sum(1 for e in in_split if e["answer_text"] is None)

        print(f"{split:10} {len(in_split):>4} examples | {origins} | no answer: {no_answer}")


if __name__ == "__main__":
    main()
