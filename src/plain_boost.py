"""
Plain-language preference: when a plain passage and a legal passage are both close matches, prefer
the plain one, because it was written for ordinary workers.

Every plain passage gets a small boost added to its similarity before the passages are re-ranked.
With the app's boost of 0.02, a plain passage overtakes a legal one only when it is within 0.02 of
it: a tie-breaker for close calls, not an override.

The app's value is fixed by design, not tuned. The validation split has no legal questions at all,
so tuning on it would always pick the biggest boost, because it cannot see the cost on legal questions.
"""

APP_BOOST = 0.02


def rerank_with_plain_boost(scored: list[tuple[str, float]], styles: dict[str, str], boost: float) -> list[str]:
    """Passage ids, best first, after adding the boost to every plain passage."""
    boosted: list[tuple[float, str]] = []

    for passage_id, score in scored:
        if styles[passage_id] == "plain":
            score = score + boost

        boosted.append((score, passage_id))

    boosted.sort(reverse=True)

    return [passage_id for _, passage_id in boosted]
