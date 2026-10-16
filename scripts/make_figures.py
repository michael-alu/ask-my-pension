"""
Draw the report's figures from the saved results, so every chart matches the numbers in results/.

Run from the project root, after the experiments:
    python scripts/make_figures.py
The figures are saved as PNG files in results/figures/.
"""

import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RESULTS = PROJECT_ROOT / "results"
FIGURES = RESULTS / "figures"

SHARES = [25, 50, 75, 100]


def load(file_name: str) -> Any:
    return json.loads((RESULTS / file_name).read_text(encoding="utf-8"))


def retriever_file(share: int) -> str:
    return f"dense_retriever-bge-small-en-v1.5-{share}pct_results.json"


def reader_file(share: int, strategy: str) -> str:
    return f"reader_reader-roberta-base-squad2-{share}pct-{strategy}_bm25_results.json"


def save(figure: Any, file_name: str) -> None:
    figure.tight_layout()

    figure.savefig(FIGURES / file_name, dpi=200, bbox_inches="tight")

    plt.close(figure)

    print(f"saved results/figures/{file_name}")


def draw_pipeline() -> None:
    steps = [
        "Question",
        "Retriever\n(fine-tuned bge-small,\ntop 30 passages)",
        "Plain boost\n(+0.02, keep top 3)",
        "Reader\n(fine-tuned roberta)",
        "Answer or refusal\n+ glossary terms\n+ source passage",
    ]

    figure, axes = plt.subplots(figsize=(11, 2.2))

    axes.set_xlim(0, len(steps))
    axes.set_ylim(0, 1)
    axes.axis("off")

    for position, step in enumerate(steps):
        axes.text(
            position + 0.5,
            0.5,
            step,
            ha="center",
            va="center",
            fontsize=9,
            bbox={"boxstyle": "round,pad=0.5", "facecolor": "#e8f0fe", "edgecolor": "#1a56db"},
        )

        if position < len(steps) - 1:
            axes.annotate("", xy=(position + 1.12, 0.5), xytext=(position + 0.88, 0.5), arrowprops={"arrowstyle": "->"})

    save(figure, "figure1_pipeline.png")


def draw_data_size() -> None:
    retriever_all = []
    retriever_own = []

    for share in SHARES:
        test = load(retriever_file(share))

        retriever_all.append(test["test/all"]["recall_at_1"])
        retriever_own.append(test["test/origin=own"]["recall_at_1"])

    reader_faq = []
    reader_own = []
    reader_refusal = []

    for share in SHARES:
        result = load(reader_file(share, "matched"))

        gold = result["test/gold_passage"]

        reader_faq.append(gold["origin=faq_rule"]["f1"])
        reader_own.append(gold["origin=own"]["answerable_f1"])
        reader_refusal.append(result["out_of_domain"]["refusal_rate"])

    figure, (left, right) = plt.subplots(1, 2, figsize=(10, 4))

    left.plot(SHARES, retriever_all, marker="o", label="All test questions")
    left.plot(SHARES, retriever_own, marker="o", label="Hand-written questions")
    left.set_title("Retriever (fine-tuned bge-small)")
    left.set_xlabel("Share of training data (%)")
    left.set_ylabel("Recall@1")

    right.plot(SHARES, reader_faq, marker="o", label="FAQ F1 (correct passage given)")
    right.plot(SHARES, reader_own, marker="o", label="Hand-written answerable F1 (correct passage given)")
    right.plot(SHARES, reader_refusal, marker="o", label="Out-of-domain refusal rate")
    right.set_title("Reader (fine-tuned roberta, matched)")
    right.set_xlabel("Share of training data (%)")
    right.set_ylabel("Score")

    for axes in [left, right]:
        axes.set_xticks(SHARES)
        axes.set_ylim(0, 1)
        axes.grid(alpha=0.3)
        axes.legend(fontsize=8)

    save(figure, "figure3_data_size.png")


def draw_shortcut() -> None:
    random_scores = []
    matched_scores = []

    for share in SHARES:
        random_result = load(reader_file(share, "random"))
        matched_result = load(reader_file(share, "matched"))

        random_scores.append(random_result["test/gold_passage"]["style=legal"]["answerable_f1"])
        matched_scores.append(matched_result["test/gold_passage"]["style=legal"]["answerable_f1"])

    figure, axes = plt.subplots(figsize=(6, 4))

    axes.plot(SHARES, random_scores, marker="o", label="Random no-answer passages")
    axes.plot(SHARES, matched_scores, marker="o", label="Matched no-answer passages")
    axes.set_title("Reader on answerable legal questions")
    axes.set_xlabel("Share of training data (%)")
    axes.set_ylabel("F1 (correct passage given)")
    axes.set_xticks(SHARES)
    axes.set_ylim(0, 1)
    axes.grid(alpha=0.3)
    axes.legend(fontsize=8)

    save(figure, "figure2_shortcut.png")


def draw_plain_boost() -> None:
    boost_file = "plain_boost_retriever-bge-small-en-v1.5-100pct_reader-roberta-base-squad2-100pct-matched.json"

    boosts = load(boost_file)["boosts"]

    sizes = [float(size) for size in boosts]

    plain_share = [boosts[size]["answers_from_plain_passages"] for size in boosts]
    legal_recall = [boosts[size]["retrieval"]["style=legal"]["recall_at_1"] for size in boosts]
    reading_ease = [boosts[size]["answer_passage_reading_ease"] for size in boosts]

    figure, (left, right) = plt.subplots(1, 2, figsize=(10, 4))

    left.plot(sizes, plain_share, marker="o", label="Answers from plain passages")
    left.plot(sizes, legal_recall, marker="o", label="Legal questions Recall@1")
    left.set_title("What the boost changes")
    left.set_xlabel("Plain boost")
    left.set_ylabel("Share / Recall@1")
    left.set_ylim(0, 1)
    left.legend(fontsize=8)

    right.plot(sizes, reading_ease, marker="o", color="tab:green")
    right.set_title("Reading ease of the answer's passage")
    right.set_xlabel("Plain boost")
    right.set_ylabel("Flesch Reading Ease (higher is easier)")
    right.set_ylim(0, 60)

    for axes in [left, right]:
        axes.axvline(0.02, color="grey", linestyle="--", linewidth=1)
        axes.grid(alpha=0.3)

    save(figure, "figure4_plain_boost.png")


def draw_error_outcomes() -> None:
    counts: dict[str, int] = load("error_analysis.json")["counts"]

    outcomes = list(counts.keys())
    numbers = list(counts.values())

    figure, axes = plt.subplots(figsize=(8, 4))

    axes.barh(outcomes, numbers, color="#1a56db")
    axes.invert_yaxis()
    axes.set_title("Outcome for each of the 134 test questions (final system)")
    axes.set_xlabel("Number of questions")

    for row, number in enumerate(numbers):
        axes.text(number + 0.5, row, str(number), va="center", fontsize=8)

    save(figure, "figure5_error_outcomes.png")


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)

    draw_pipeline()
    draw_shortcut()
    draw_data_size()
    draw_plain_boost()
    draw_error_outcomes()


if __name__ == "__main__":
    main()
