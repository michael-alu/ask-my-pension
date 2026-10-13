"""
The plain-language preference experiment: what does favouring plain passages do to accuracy and to
how easy the answers are to read?

For several boost sizes, the dense retriever's top 30 passages are re-ranked with the boost, then:
- retrieval is scored (Recall@1, Recall@5) overall, for FAQ and own questions, and for plain and legal
- the reader answers from the new top 3, scored with F1
- readability is measured as the Flesch Reading Ease of the top passage and of the passage the answer
  came from (higher is easier)

The sweep is an analysis on test, not a way to pick a value: the app's boost (0.02) is fixed in advance.

Run from the project root, after the retriever and reader have been evaluated with evaluate_reader.py
(its tuned no-answer threshold is reused, so the reader behaves exactly as in the experiments table):
    python scripts/evaluate_plain_boost.py models/retriever-bge-small-en-v1.5-100pct models/reader-roberta-base-squad2-100pct-matched
"""

import json
import statistics
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import Passage, RetrievalPrediction, SquadExample  # noqa: E402
from src.dense_retrieval import embed, load_dense_model, search_dense_scored  # noqa: E402
from src.eval_questions import load_eval_questions  # noqa: E402
from src.experiments import record_experiment  # noqa: E402
from src.metrics import retrieval_summary  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402
from src.plain_boost import APP_BOOST, rerank_with_plain_boost  # noqa: E402
from src.qa_metrics import qa_summary  # noqa: E402
from src.reader import decide_across_passages, load_reader, read  # noqa: E402
from src.retrieval_eval import make_prediction, slice_value  # noqa: E402
from src.splits import load_splits  # noqa: E402

RESULTS_FOLDER = PROJECT_ROOT / "results"

SQUAD_TEST_FILE = PROJECT_ROOT / "data" / "squad" / "test.jsonl"

BOOSTS = [0.0, 0.01, 0.02, 0.03, 0.05, 0.1]

CANDIDATES = 30

PASSAGES_TO_READ = 3


def short_name_of(model_name: str) -> str:
    return model_name.rstrip("/").split("/")[-1]


def tuned_threshold(reader_name: str, retriever_name: str) -> float:
    results_file = RESULTS_FOLDER / f"reader_{short_name_of(reader_name)}_{short_name_of(retriever_name)}_results.json"

    if not results_file.exists():
        raise SystemExit(f"Run evaluate_reader.py {reader_name} {retriever_name} first, to tune the threshold.")

    results = json.loads(results_file.read_text(encoding="utf-8"))

    threshold: float = results["tuned_threshold"]

    return threshold


def retrieval_scores(predictions: list[RetrievalPrediction], reading_ease: dict[str, float]) -> dict[str, float]:
    ranks = [p["rank"] for p in predictions]

    return retrieval_summary(ranks, [reading_ease[p["top_ids"][0]] for p in predictions])


def answer_with_reads(
    reader: Any, question: str, passage_ids: list[str], passages_by_id: dict[str, Passage], cache: dict[tuple[str, str], tuple[str, float]]
) -> list[tuple[str, float, str]]:
    """Read each passage once, remembering the result, because the same passage comes up for several boosts."""
    reads = []

    for passage_id in passage_ids:
        key = (question, passage_id)

        if key not in cache:
            cache[key] = read(reader, question, passages_by_id[passage_id]["text"])

        answer, margin = cache[key]

        reads.append((answer, margin, passage_id))

    return reads


def main() -> None:
    retriever_name = sys.argv[1] if len(sys.argv) > 1 else "models/retriever-bge-small-en-v1.5-100pct"

    reader_name = sys.argv[2] if len(sys.argv) > 2 else "models/reader-roberta-base-squad2-100pct-matched"

    threshold = tuned_threshold(reader_name, retriever_name)

    passages = load_searchable_passages()

    passages_by_id = {p["passage_id"]: p for p in passages}

    styles = {p["passage_id"]: p["style"] for p in passages}

    reading_ease = {p["passage_id"]: p["reading_ease"] for p in passages}

    test_questions = [q for q in load_eval_questions(passages_by_id, load_splits()) if q["split"] == "test"]

    with open(SQUAD_TEST_FILE, encoding="utf-8") as file:
        test_examples: list[SquadExample] = [json.loads(line) for line in file]

    model = load_dense_model(retriever_name)

    passage_embeddings = embed(model, [p["text"] for p in passages])

    all_question_texts = {q["question"] for q in test_questions} | {e["question"] for e in test_examples}

    candidates = {text: search_dense_scored(model, passage_embeddings, passages, text, CANDIDATES) for text in all_question_texts}

    reader = load_reader(reader_name)

    cache: dict[tuple[str, str], tuple[str, float]] = {}

    results: dict[str, Any] = {"retriever": retriever_name, "reader": reader_name, "threshold": threshold, "boosts": {}}

    for boost in BOOSTS:
        predictions = [
            make_prediction(q, rerank_with_plain_boost(candidates[q["question"]], styles, boost)[:10]) for q in test_questions
        ]

        retrieval = {"all": retrieval_scores(predictions, reading_ease)}

        for slice_name, value in [("origin", "faq"), ("origin", "own"), ("style", "plain"), ("style", "legal")]:
            group = [p for p in predictions if slice_value(p, slice_name) == value]

            retrieval[f"{slice_name}={value}"] = retrieval_scores(group, reading_ease)

        answers = []

        answer_passage_ids = []

        for example in test_examples:
            top_ids = rerank_with_plain_boost(candidates[example["question"]], styles, boost)[:PASSAGES_TO_READ]

            reads = answer_with_reads(reader, example["question"], top_ids, passages_by_id, cache)

            answer, passage_id = decide_across_passages(reads, threshold)

            answers.append(answer)

            answer_passage_ids.append(passage_id)

        golds = [e["answer_text"] for e in test_examples]

        own_positions = [i for i, e in enumerate(test_examples) if e["origin"] == "own"]

        answered_ease = [reading_ease[pid] for pid in answer_passage_ids if pid is not None]

        answered_plain = sum(1 for pid in answer_passage_ids if pid is not None and styles[pid] == "plain")

        results["boosts"][str(boost)] = {
            "retrieval": retrieval,
            "end_to_end": qa_summary(answers, golds),
            "end_to_end_own": qa_summary([answers[i] for i in own_positions], [golds[i] for i in own_positions]),
            "answer_passage_reading_ease": round(statistics.mean(answered_ease), 1) if answered_ease else 0.0,
            "answers_from_plain_passages": round(answered_plain / max(len(answered_ease), 1), 3),
        }

    stem = f"plain_boost_{short_name_of(retriever_name)}_{short_name_of(reader_name)}"

    RESULTS_FOLDER.mkdir(parents=True, exist_ok=True)

    (RESULTS_FOLDER / f"{stem}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    record_app_boost_row(results, retriever_name, reader_name)

    print_table(results)


def record_app_boost_row(results: dict[str, Any], retriever_name: str, reader_name: str) -> None:
    app = results["boosts"][str(APP_BOOST)]

    record_experiment(
        {
            "experiment": f"{short_name_of(retriever_name)} + plain boost {APP_BOOST} + reader {short_name_of(reader_name)}, end to end",
            "split": "test",
            "questions": app["end_to_end"]["questions"],
            "recall_at_1": app["retrieval"]["all"]["recall_at_1"],
            "recall_at_5": app["retrieval"]["all"]["recall_at_5"],
            "mrr_at_10": app["retrieval"]["all"]["mrr_at_10"],
            "exact_match": app["end_to_end"]["exact_match"],
            "f1": app["end_to_end"]["f1"],
            "top1_reading_ease": app["answer_passage_reading_ease"],
            "notes": f"reading ease is of the passage each answer came from; "
            f"{app['answers_from_plain_passages']:.0%} of answers come from plain passages",
        }
    )


def print_table(results: dict[str, Any]) -> None:
    print(f"retriever: {results['retriever']} | reader: {results['reader']} | threshold: {results['threshold']}")

    header = f"{'boost':>6} {'R@1 all':>8} {'R@1 own':>8} {'R@1 legal':>9} {'R@5 legal':>9} {'e2e F1':>7} {'own F1':>7} {'ease top1':>9} {'ease answer':>11} {'plain answers':>13}"

    print(header)

    for boost, row in results["boosts"].items():
        retrieval = row["retrieval"]

        print(
            f"{boost:>6} {retrieval['all']['recall_at_1']:>8} {retrieval['origin=own']['recall_at_1']:>8}"
            f" {retrieval['style=legal']['recall_at_1']:>9} {retrieval['style=legal']['recall_at_5']:>9}"
            f" {row['end_to_end']['f1']:>7} {row['end_to_end_own']['f1']:>7} {retrieval['all']['top1_reading_ease']:>9}"
            f" {row['answer_passage_reading_ease']:>11} {row['answers_from_plain_passages']:>13.0%}"
        )


if __name__ == "__main__":
    main()
