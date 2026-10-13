"""
Put together the folder that gets uploaded to Hugging Face Spaces, with only what the app needs.

The app needs its code, the two fine-tuned models, the saved passage embeddings, the passages it
answers from, the source list (for document names and links), the exclusion files, the glossary,
and the results file that holds the tuned no-answer threshold. Nothing else is copied, so the raw
documents and the annotations stay out of the Space.

Run from the project root, after the app has been started once locally (that saves the embeddings):
    python scripts/prepare_space.py
Then upload the space/ folder to Hugging Face (see the README).
"""

import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SPACE_FOLDER = PROJECT_ROOT / "space"

FILES_TO_COPY = [
    "app/app.py",
    "src/__init__.py",
    "src/answer_pipeline.py",
    "src/data_types.py",
    "src/dense_retrieval.py",
    "src/glossary.py",
    "src/passages.py",
    "src/plain_boost.py",
    "src/reader.py",
    "src/review_files.py",
    "data/processed/passages.jsonl",
    "data/sources.csv",
    "data/annotations/excluded_passages.csv",
    "data/annotations/number_review.csv",
    "data/glossary/glossary.csv",
    "results/reader_reader-roberta-base-squad2-100pct-matched_retriever-bge-small-en-v1.5-100pct_results.json",
    "models/passage_embeddings.npy",
]

FOLDERS_TO_COPY = [
    "models/retriever-bge-small-en-v1.5-100pct",
    "models/reader-roberta-base-squad2-100pct-matched",
]

SPACE_README = """---
title: Ask My Pension
colorFrom: green
colorTo: gray
sdk: gradio
sdk_version: 5.50.0
python_version: "3.10"
app_file: app/app.py
pinned: false
---

# Ask My Pension

A student project: a question answering assistant for the Nigerian Contributory Pension Scheme.
Answers are taken from pension documents published by the National Pension Commission (PenCom)
and pension fund administrators, and the source of every answer is shown. Not official financial
or legal advice, and not connected to or endorsed by PenCom or any pension company.

Code, data preparation, training and evaluation: https://github.com/michael-alu/ask-my-pension
"""

SPACE_REQUIREMENTS = """torch
transformers>=4.44,<5
sentence-transformers>=3,<5
huggingface-hub<1.0
numpy<2
"""


def main() -> None:
    missing = [path for path in FILES_TO_COPY + FOLDERS_TO_COPY if not (PROJECT_ROOT / path).exists()]

    if missing:
        raise SystemExit(f"Missing, so the Space would not work: {missing}")

    if SPACE_FOLDER.exists():
        shutil.rmtree(SPACE_FOLDER)

    for path in FILES_TO_COPY:
        target = SPACE_FOLDER / path

        target.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(PROJECT_ROOT / path, target)

    for path in FOLDERS_TO_COPY:
        shutil.copytree(PROJECT_ROOT / path, SPACE_FOLDER / path)

    (SPACE_FOLDER / "README.md").write_text(SPACE_README, encoding="utf-8")

    (SPACE_FOLDER / "requirements.txt").write_text(SPACE_REQUIREMENTS, encoding="utf-8")

    total_bytes = sum(file.stat().st_size for file in SPACE_FOLDER.rglob("*") if file.is_file())

    print(f"space/ is ready: {total_bytes / 1_000_000:.0f} MB")


if __name__ == "__main__":
    main()
