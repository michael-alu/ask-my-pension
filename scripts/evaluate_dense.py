"""
Evaluate a dense retriever, either an off-the-shelf model or one fine-tuned by train_retriever.py.

It is scored exactly like BM25, so the numbers can be compared directly.

Run from the project root:
    python scripts/evaluate_dense.py BAAI/bge-small-en-v1.5
    python scripts/evaluate_dense.py models/retriever-bge-small-en-v1.5-100pct
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.dense_retrieval import embed, load_dense_model, search_dense  # noqa: E402
from src.eval_questions import load_eval_questions  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.retrieval_eval import TOP_K, evaluate_retriever  # noqa: E402
from src.splits import load_splits  # noqa: E402

DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"


def main() -> None:
    model_name = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL

    short_name = model_name.rstrip("/").split("/")[-1]

    is_fine_tuned = model_name.startswith("models/")

    experiment_name = f"Dense retriever {short_name}" + ("" if is_fine_tuned else " (zero-shot)")

    passages = load_searchable_passages()

    passages_by_id = {p["passage_id"]: p for p in passages}

    reading_ease = {p["passage_id"]: p["reading_ease"] for p in passages}

    questions = load_eval_questions(passages_by_id, load_splits())

    model = load_dense_model(model_name)

    passage_embeddings = embed(model, [p["text"] for p in passages])

    rankings = [search_dense(model, passage_embeddings, passages, q["question"], TOP_K) for q in questions]

    results_file = PROJECT_ROOT / "results" / f"dense_{short_name}_results.json"

    predictions_file = PROJECT_ROOT / "results" / f"dense_{short_name}_predictions.jsonl"

    evaluate_retriever(rankings, questions, reading_ease, experiment_name, results_file, predictions_file)


if __name__ == "__main__":
    main()
