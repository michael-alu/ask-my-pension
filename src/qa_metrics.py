"""
The standard SQuAD 2.0 answer metrics.

- Exact Match: 1 if the predicted answer is the same as the gold answer, after both are cleaned
  (lowercase, no punctuation, no "a", "an", "the", single spaces). Otherwise 0.
- F1: partial credit for overlapping words. Precision is the share of predicted words that are
  in the gold answer, recall is the share of gold words that were predicted, and F1 combines them.
- For a no-answer question, both are 1 only when the model also gives no answer.
"""

import re
import statistics
import string
from collections import Counter

ARTICLES = re.compile(r"\b(a|an|the)\b")


def normalise(text: str) -> str:
    text = text.lower()

    text = "".join(character for character in text if character not in string.punctuation)

    text = ARTICLES.sub(" ", text)

    return " ".join(text.split())


def exact_match(prediction: str, gold: str | None) -> float:
    if gold is None:
        return 1.0 if prediction == "" else 0.0

    return 1.0 if normalise(prediction) == normalise(gold) else 0.0


def f1(prediction: str, gold: str | None) -> float:
    if gold is None or prediction == "":
        return exact_match(prediction, gold)

    predicted_words = normalise(prediction).split()

    gold_words = normalise(gold).split()

    shared = sum((Counter(predicted_words) & Counter(gold_words)).values())

    if shared == 0:
        return 0.0

    precision = shared / len(predicted_words)

    recall = shared / len(gold_words)

    return 2 * precision * recall / (precision + recall)


def qa_summary(predictions: list[str], golds: list[str | None]) -> dict[str, float]:
    exact_scores = [exact_match(p, g) for p, g in zip(predictions, golds)]

    f1_scores = [f1(p, g) for p, g in zip(predictions, golds)]

    answerable_f1 = [score for score, gold in zip(f1_scores, golds) if gold is not None]

    no_answer_correct = [score for score, gold in zip(exact_scores, golds) if gold is None]

    return {
        "questions": len(predictions),
        "exact_match": round(statistics.mean(exact_scores), 3),
        "f1": round(statistics.mean(f1_scores), 3),
        "answerable_f1": round(statistics.mean(answerable_f1), 3) if answerable_f1 else 0.0,
        "no_answer_accuracy": round(statistics.mean(no_answer_correct), 3) if no_answer_correct else 0.0,
        "answerable": len(answerable_f1),
        "no_answer": len(no_answer_correct),
    }
