"""
The reader: a SQuAD 2.0 model that points at the answer span in a passage, or says there is none.

For each question and passage, the model gives a score to its best span and a score to "no
answer". We answer only when the best span beats "no answer" by more than a threshold. A
threshold of 0 is the model's own default. It is tuned on the validation split, never on test.
"""

from typing import Any

from transformers import pipeline


def load_reader(model_name: str) -> Any:
    return pipeline("question-answering", model=model_name, device=-1)


def read(reader: Any, question: str, context: str) -> tuple[str, float, float]:
    """Return the best answer span, its score, and the score for "no answer"."""
    results = reader(question=question, context=context, handle_impossible_answer=True, top_k=5)

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

    return best_answer, best_score, no_answer_score


def decide(best_answer: str, best_score: float, no_answer_score: float, threshold: float) -> str:
    """The final answer, or "" when the model should stay quiet."""
    if best_answer and best_score - no_answer_score > threshold:
        return best_answer

    return ""
