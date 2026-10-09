"""
A small local web page for writing annotations.

Press "Random passage", write a question a real worker might ask about it, highlight the answer
and save. Or write a question the passage sounds related to but does NOT answer, and press
"No answer in this passage". You stay on the same passage, so you can write several questions.

FAQ questions are not annotated here. Their answers are used whole, by rule, when the
training file is built.

Annotations are saved to data/annotations/annotations.jsonl.

Run from the project root:
    python scripts/annotation_tool.py
"""

import json
import random
import sys
from pathlib import Path

import gradio as gr

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.annotations import (  # noqa: E402
    find_answer_start,
    load_annotations,
    progress_report,
    save_annotations,
)
from src.data_types import Annotation, Passage  # noqa: E402
from src.review_files import load_excluded_ids  # noqa: E402
from src.splits import load_splits, split_of  # noqa: E402

PASSAGES_FILE = PROJECT_ROOT / "data" / "processed" / "passages.jsonl"

Screen = tuple[str, str, str, str | None, str]


def read_passages() -> list[Passage]:
    with open(PASSAGES_FILE, encoding="utf-8") as file:
        return [json.loads(line) for line in file]


SPLITS = load_splits()

EXCLUDED_IDS = load_excluded_ids()

PASSAGES = [p for p in read_passages() if p["passage_id"] not in EXCLUDED_IDS]

PASSAGES_BY_ID = {p["passage_id"]: p for p in PASSAGES}


def show(passage_id: str, status: str) -> Screen:
    """Everything on screen: passage text, question, answer, current passage id, and the message."""
    passage = PASSAGES_BY_ID[passage_id]

    info = f"`{passage_id}` | {passage['style']} | split: {split_of(passage, SPLITS)} | {passage['section']}"

    progress = progress_report(load_annotations(), PASSAGES_BY_ID, SPLITS)

    message = f"{status}  \n{info}  \n\n{progress}"

    return passage["text"], "", "", passage_id, message


def random_passage(style: str, split: str) -> Screen:
    candidates = []

    for passage in PASSAGES:
        if style != "any" and passage["style"] != style:
            continue

        if split != "any" and split_of(passage, SPLITS) != split:
            continue

        candidates.append(passage)

    if not candidates:
        return "", "", "", None, "No passages match these filters."

    passage = random.choice(candidates)

    return show(passage["passage_id"], "")


def add_annotation(
    passage_id: str, question: str, answer: str | None, level: str
) -> str:
    answer_start = None

    annotations = load_annotations()

    passage = PASSAGES_BY_ID[passage_id]

    if answer is not None:
        answer_start = find_answer_start(passage["text"], answer)

    annotation: Annotation = {
        "level": level,
        "question": question,
        "answer_text": answer,
        "passage_id": passage_id,
        "answer_start": answer_start,
        "annotation_id": f"a{len(annotations) + 1:04d}",
        "from_faq": question == passage["faq_question"],
    }

    annotations.append(annotation)

    save_annotations(annotations)

    return f"Saved {annotation['annotation_id']}. Write another question on this passage, or pick a new one."


def problem_with(
    passage_id: str | None, question: str, answer: str | None, level: str | None
) -> str | None:
    if passage_id is None:
        return "Press 'Random passage' first."

    if not question.strip():
        return "Write a question first."

    if level is None:
        return "Pick beginner or detailed first."

    if (
        answer is not None
        and find_answer_start(PASSAGES_BY_ID[passage_id]["text"], answer) is None
    ):
        return "That answer is not in the passage. Highlight it in the passage box."

    return None


def stay(passage_id: str | None, question: str, answer: str, problem: str) -> Screen:
    """Keep everything on screen and show what needs fixing."""
    passage_text = ""

    if passage_id is not None:
        passage_text = PASSAGES_BY_ID[passage_id]["text"]

    return passage_text, question, answer, passage_id, f"**{problem}**"


def save(
    passage_id: str | None, question: str, answer: str, level: str | None
) -> Screen:
    answer = answer.strip()

    problem = problem_with(passage_id, question, answer, level)

    if problem or passage_id is None or level is None:
        return stay(passage_id, question, answer, problem or "")

    status = add_annotation(passage_id, question.strip(), answer, level)

    return show(passage_id, status)


def save_no_answer(passage_id: str | None, question: str, level: str | None) -> Screen:
    problem = problem_with(passage_id, question, None, level)

    if problem or passage_id is None or level is None:
        return stay(passage_id, question, "", problem or "")

    status = add_annotation(passage_id, question.strip(), None, level)

    return show(passage_id, status)


def undo() -> str:
    annotations = load_annotations()

    if not annotations:
        return "Nothing to undo."

    removed = annotations.pop()

    save_annotations(annotations)

    return f"Deleted {removed['annotation_id']}: {removed['question']}"


def copy_selection(event: gr.SelectData) -> str:
    selected_text: str = event.value

    return selected_text


with gr.Blocks(title="Annotation tool") as page:
    current_id = gr.State(None)

    with gr.Row():
        random_button = gr.Button("Random passage")

        style_box = gr.Dropdown(["any", "plain", "legal"], value="legal", label="Style")

        split_box = gr.Dropdown(
            ["any", "train", "validation", "test"], value="test", label="Split"
        )

    message_box = gr.Markdown()

    passage_box = gr.Textbox(
        label="Passage: highlight the answer with your mouse",
        lines=10,
        interactive=False,
    )

    question_box = gr.Textbox(label="Your question, the way a real worker would ask it")

    answer_box = gr.Textbox(label="Answer (filled in when you highlight)")

    level_box = gr.Radio(
        ["beginner", "detailed"],
        label="beginner: what is X, why, what if | detailed: rules, steps",
    )

    with gr.Row():
        save_button = gr.Button("Save", variant="primary")

        no_answer_button = gr.Button("No answer in this passage")

        undo_button = gr.Button("Undo last save", variant="stop")

    screen = [passage_box, question_box, answer_box, current_id, message_box]

    random_button.click(random_passage, inputs=[style_box, split_box], outputs=screen)

    save_button.click(
        save, inputs=[current_id, question_box, answer_box, level_box], outputs=screen
    )

    no_answer_button.click(
        save_no_answer, inputs=[current_id, question_box, level_box], outputs=screen
    )

    undo_button.click(undo, outputs=[message_box])

    passage_box.select(copy_selection, outputs=[answer_box])


if __name__ == "__main__":
    page.launch()
