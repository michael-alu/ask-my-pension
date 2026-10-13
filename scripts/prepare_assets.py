"""
Put together the files the deployed app downloads from Hugging Face: the two fine-tuned models,
the passages and their saved embeddings. They go into an assets/ folder with the same layout as
the project, so the app can download them straight into place.

Run from the project root, after the app has been started once locally (that saves the embeddings):
    python scripts/prepare_assets.py
Then upload the assets/ folder to a private Hugging Face model repository (see the README).
"""

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.assets import NEEDED  # noqa: E402

ASSETS_FOLDER = PROJECT_ROOT / "assets"

MODEL_CARD = """# Ask My Pension: app assets

Private files for the Ask My Pension student project: a fine-tuned bge-small retriever, a fine-tuned
roberta-base SQuAD 2.0 reader, the document passages the app answers from, and their embeddings.
The passages are quoted from documents published by the National Pension Commission (PenCom) and
pension fund administrators, which own them.

Code, data preparation, training and evaluation: https://github.com/michael-alu/ask-my-pension
"""


def main() -> None:
    missing = [path for path in NEEDED if not (PROJECT_ROOT / path).exists()]

    if missing:
        raise SystemExit(f"Missing, so the app would not work: {missing}. Start the app once locally first.")

    if ASSETS_FOLDER.exists():
        shutil.rmtree(ASSETS_FOLDER)

    for path in NEEDED:
        source = PROJECT_ROOT / path

        target = ASSETS_FOLDER / path

        target.parent.mkdir(parents=True, exist_ok=True)

        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copy2(source, target)

    (ASSETS_FOLDER / "README.md").write_text(MODEL_CARD, encoding="utf-8")

    total_bytes = sum(file.stat().st_size for file in ASSETS_FOLDER.rglob("*") if file.is_file())

    print(f"assets/ is ready: {total_bytes / 1_000_000:.0f} MB")


if __name__ == "__main__":
    main()
