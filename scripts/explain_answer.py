"""
Show every step the system takes to answer one question, so you can see how the pieces connect.

1. BM25, the baseline, for comparison: its top 3 passages.
2. The fine-tuned dense retriever: its top 5 passages and their similarity scores.
3. The plain boost: the 3 passages the reader will read, after plain passages get +0.02.
4. The reader: its answer for each of the 3 passages, and the margin over "no answer".
5. The decision: the answer with the highest margin, if it beats the threshold.

Run from the project root, with the models in models/:
    python scripts/explain_answer.py "What is an RSA?"
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.answer_pipeline import CANDIDATES, PASSAGES_TO_READ, System, load_system  # noqa: E402
from src.dense_retrieval import search_dense_scored  # noqa: E402
from src.glossary import terms_in  # noqa: E402
from src.plain_boost import APP_BOOST, rerank_with_plain_boost  # noqa: E402
from src.reader import decide_across_passages, read  # noqa: E402
from src.retrieval import build_bm25, search_bm25  # noqa: E402

PREVIEW_LENGTH = 100

DENSE_TO_SHOW = 5


def preview(system: System, passage_id: str) -> str:
    passage = system["passages_by_id"][passage_id]

    short_text = passage["text"][:PREVIEW_LENGTH]

    return f"[{passage['style']}] {passage_id}: {short_text}..."


def explain(system: System, question: str) -> None:
    print(f"\nQUESTION: {question}")

    print("\n1. BM25 baseline, top 3 (word matching only):")

    bm25 = build_bm25(system["passages"])

    bm25_ids = search_bm25(bm25, system["passages"], question, PASSAGES_TO_READ)

    for passage_id in bm25_ids:
        print(f"   {preview(system, passage_id)}")

    print(f"\n2. Fine-tuned dense retriever, top {DENSE_TO_SHOW} of {CANDIDATES} (cosine similarity):")

    scored = search_dense_scored(system["retriever"], system["embeddings"], system["passages"], question, CANDIDATES)

    for passage_id, similarity in scored[:DENSE_TO_SHOW]:
        print(f"   {similarity:.3f}  {preview(system, passage_id)}")

    print(f"\n3. After the plain boost (+{APP_BOOST}), the {PASSAGES_TO_READ} passages the reader reads:")

    top_ids = rerank_with_plain_boost(scored, system["styles"], APP_BOOST)[:PASSAGES_TO_READ]

    for passage_id in top_ids:
        print(f"   {preview(system, passage_id)}")

    print("\n4. The reader on each passage (margin = best answer score minus no-answer score):")

    reads = []

    for passage_id in top_ids:
        passage_text = system["passages_by_id"][passage_id]["text"]

        answer, margin = read(system["reader"], question, passage_text)

        reads.append((answer, margin, passage_id))

        shown_answer = answer if answer else "(no answer)"

        print(f"   margin {margin:+.3f}  {passage_id}: {shown_answer}")

    threshold = system["threshold"]

    print(f"\n5. Decision (answer only if a margin is above the threshold {threshold}):")

    best_answer, best_passage_id = decide_across_passages(reads, threshold)

    if best_passage_id is None:
        print("   REFUSED: no margin beat the threshold.")

        return

    print(f"   ANSWER from {best_passage_id}: {best_answer}")

    passage_text = system["passages_by_id"][best_passage_id]["text"]

    found_terms = terms_in(best_answer + " " + passage_text, system["glossary"])

    term_names = [entry["term"] for entry in found_terms]

    print(f"   Glossary terms shown: {term_names}")


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit('Usage: python scripts/explain_answer.py "your question"')

    question = sys.argv[1]

    print("Loading the models (takes a few seconds)...")

    system = load_system()

    explain(system, question)


if __name__ == "__main__":
    main()
