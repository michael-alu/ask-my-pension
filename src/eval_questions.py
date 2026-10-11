"""
The questions every model is evaluated on.

- FAQ questions: the gold passage is the FAQ answer itself.
- Your own questions: the gold passage is the one you annotated. No-answer questions are
  left out here, because retrieval needs a passage to find.

The level (beginner or detailed) of an FAQ question comes from faq_levels.csv, or from
an FAQ question you annotated in the tool. Otherwise it is "unlabelled".
"""

from src.annotations import load_annotations
from src.data_types import Annotation, EvalQuestion, Passage
from src.review_files import FAQ_LEVELS_FILE, read_rows
from src.splits import split_of


def load_faq_levels(annotations: list[Annotation]) -> dict[str, str]:
    levels: dict[str, str] = {}

    for annotation in annotations:
        if annotation["from_faq"]:
            levels[annotation["passage_id"]] = annotation["level"]

    for row in read_rows(FAQ_LEVELS_FILE):
        level = row["level"].strip().lower()

        if level:
            levels[row["passage_id"]] = level

    return levels


def load_eval_questions(passages_by_id: dict[str, Passage], splits: dict[str, str]) -> list[EvalQuestion]:
    annotations = load_annotations()

    faq_levels = load_faq_levels(annotations)

    questions: list[EvalQuestion] = []

    for passage in passages_by_id.values():
        faq_question = passage["faq_question"]

        if faq_question is None:
            continue

        questions.append(
            {
                "question": faq_question,
                "gold_passage_id": passage["passage_id"],
                "origin": "faq",
                "level": faq_levels.get(passage["passage_id"], "unlabelled"),
                "split": split_of(passage, splits),
                "style": passage["style"],
            }
        )

    for annotation in annotations:
        if annotation["from_faq"] or annotation["answer_text"] is None:
            continue

        annotated_passage = passages_by_id.get(annotation["passage_id"])

        if annotated_passage is None:
            continue

        questions.append(
            {
                "question": annotation["question"],
                "gold_passage_id": annotated_passage["passage_id"],
                "origin": "own",
                "level": annotation["level"],
                "split": split_of(annotated_passage, splits),
                "style": annotated_passage["style"],
            }
        )

    return questions
