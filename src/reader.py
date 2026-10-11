"""
The reader: a SQuAD 2.0 model that points at the answer span in a passage, or says there is none.

For each question and passage, the model gives a score to its best span and a score to "no
answer". The margin is the first minus the second. We answer only when the margin is above a
threshold. A threshold of 0 is the model's own default. The threshold is tuned on the
validation split, never on test.

Answers may be up to 300 tokens long. The pipeline's hidden default is 15 tokens, which silently
cut off our gold answers (median 34 words) and made fine-tuned readers look broken.
"""

from typing import Any

import torch
from transformers import pipeline

MAX_ANSWER_TOKENS = 300


def load_reader(model_name: str) -> Any:
    device = 0 if torch.cuda.is_available() else -1

    return pipeline("question-answering", model=model_name, device=device)


def read(reader: Any, question: str, context: str) -> tuple[str, float]:
    """Return the best answer span and its margin over "no answer"."""
    results = reader(
        question=question,
        context=context,
        handle_impossible_answer=True,
        top_k=5,
        max_answer_len=MAX_ANSWER_TOKENS,
    )

    if isinstance(results, dict):
        results = [results]

    no_answer_score = 0.0

    best_answer = ""

    best_score = 0.0

    for result in results:
        if result["answer"] == "":
            no_answer_score = max(no_answer_score, result["score"])
        elif not best_answer:
            best_answer = result["answer"]
            best_score = result["score"]

    return best_answer, best_score - no_answer_score


def decide(answer: str, margin: float, threshold: float) -> str:
    """The final answer, or "" when the model should stay quiet."""
    if answer and margin > threshold:
        return answer

    return ""


def decide_across_passages(reads: list[tuple[str, float, str]], threshold: float) -> tuple[str, str | None]:
    """From one read per passage, keep the answer with the highest margin. Returns it and its passage id."""
    best_answer = ""

    best_passage_id = None

    best_margin = threshold

    for answer, margin, passage_id in reads:
        if answer and margin > best_margin:
            best_answer = answer

            best_passage_id = passage_id

            best_margin = margin

    return best_answer, best_passage_id
