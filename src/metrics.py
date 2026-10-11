"""
Retrieval metrics.

- Recall@k: the share of questions whose gold passage is in the top k results.
- MRR@10: the average of 1 / rank of the gold passage (1 if first, 0.5 if second, and so on),
  counting 0 when it is not in the top 10. It rewards putting the right passage near the top.
"""

import statistics


def rank_of(ranked_ids: list[str], gold_id: str) -> int | None:
    """1 if the gold passage came first, 2 if second, None if it was not found."""
    if gold_id not in ranked_ids:
        return None

    return ranked_ids.index(gold_id) + 1


def retrieval_summary(ranks: list[int | None], top1_reading_ease: list[float]) -> dict[str, float]:
    total = len(ranks)

    found_first = sum(1 for rank in ranks if rank == 1)

    found_in_five = sum(1 for rank in ranks if rank is not None and rank <= 5)

    reciprocal_ranks = [1 / rank if rank is not None and rank <= 10 else 0.0 for rank in ranks]

    return {
        "questions": total,
        "recall_at_1": round(found_first / total, 3),
        "recall_at_5": round(found_in_five / total, 3),
        "mrr_at_10": round(statistics.mean(reciprocal_ranks), 3),
        "top1_reading_ease": round(statistics.mean(top1_reading_ease), 1),
    }
