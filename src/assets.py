"""
Files the app needs that cannot go in git: the two fine-tuned models (too big), and the passages
with their saved embeddings (they hold the publishers' text). They live in a private Hugging Face
model repository and are downloaded the first time the app starts, if they are not already on disk.

If the repository cannot be reached, huggingface_hub does not raise an error. It quietly returns
the folder as it is. So the files are checked again after downloading.

Two settings are needed, as Streamlit secrets or environment variables:
- HF_ASSETS_REPO: the repository, like "michael-alu/ask-my-pension-assets"
- HF_TOKEN: a Hugging Face token that can read it
"""

import os
from pathlib import Path

from huggingface_hub import snapshot_download

PROJECT_ROOT = Path(__file__).resolve().parent.parent

NEEDED = [
    "models/retriever-bge-small-en-v1.5-100pct",
    "models/reader-roberta-base-squad2-100pct-matched",
    "models/passage_embeddings.npy",
    "data/processed/passages.jsonl",
]


def missing_assets() -> list[str]:
    return [path for path in NEEDED if not (PROJECT_ROOT / path).exists()]


def ensure_assets() -> None:
    """Download the assets into the project folder, unless they are already there."""
    if not missing_assets():
        return

    repo = os.environ.get("HF_ASSETS_REPO")

    if not repo:
        raise RuntimeError(f"Missing {missing_assets()} and HF_ASSETS_REPO is not set, so they cannot be downloaded.")

    snapshot_download(repo_id=repo, repo_type="model", token=os.environ.get("HF_TOKEN"), local_dir=PROJECT_ROOT)

    still_missing = missing_assets()

    if still_missing:
        raise RuntimeError(
            f"Could not download {still_missing} from {repo}. Check that HF_ASSETS_REPO is spelled correctly, "
            "that HF_TOKEN can read it, and that the upload finished."
        )
