"""
Fine-tune a dense retriever on our own (question, correct passage) pairs from the train split.

The loss is Multiple Negatives Ranking Loss. In each batch, every question has its correct
passage, and the other passages in the batch act as wrong answers. The model learns to put each
question's embedding close to its correct passage and far from the others.

Batches never contain the same passage twice. Otherwise two questions about one passage would
each treat the other's correct passage as a wrong answer, and the model would learn something false.

Training uses an NVIDIA GPU when there is one (like on Colab), and the CPU otherwise.

Run from the project root, after export_squad.py. Arguments are optional:
    python scripts/train_retriever.py <base model> <share of training data> <epochs>
    python scripts/train_retriever.py BAAI/bge-small-en-v1.5 1.0 3

Saves the model to models/retriever-<base model>-<percent>pct.
"""

import json
import random
import sys
from pathlib import Path

import torch
from datasets import Dataset
from sentence_transformers import (
    SentenceTransformer,
    SentenceTransformerTrainer,
    SentenceTransformerTrainingArguments,
    losses,
)
from sentence_transformers.training_args import BatchSamplers

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import SquadExample  # noqa: E402

TRAIN_FILE = PROJECT_ROOT / "data" / "squad" / "train.jsonl"

MODELS_FOLDER = PROJECT_ROOT / "models"

SEED = 13

BATCH_SIZE = 16

LEARNING_RATE = 2e-5


def read_training_pairs() -> list[tuple[str, str]]:
    """Every answerable train question with its passage, without repeats."""
    with open(TRAIN_FILE, encoding="utf-8") as file:
        examples: list[SquadExample] = [json.loads(line) for line in file]

    pairs: list[tuple[str, str]] = []

    for example in examples:
        pair = (example["question"], example["context"])

        if example["answer_text"] is not None and pair not in pairs:
            pairs.append(pair)

    return pairs


def main() -> None:
    base_model = sys.argv[1] if len(sys.argv) > 1 else "BAAI/bge-small-en-v1.5"

    share = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 3

    short_name = base_model.rstrip("/").split("/")[-1]

    output_folder = MODELS_FOLDER / f"retriever-{short_name}-{round(share * 100)}pct"

    pairs = read_training_pairs()

    random.Random(SEED).shuffle(pairs)

    pairs = pairs[: round(len(pairs) * share)]

    train_dataset = Dataset.from_dict(
        {
            "anchor": [question for question, _ in pairs],
            "positive": [passage for _, passage in pairs],
        }
    )

    model = SentenceTransformer(base_model)

    loss = losses.MultipleNegativesRankingLoss(model)

    training_arguments = SentenceTransformerTrainingArguments(
        output_dir=str(MODELS_FOLDER / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        warmup_ratio=0.1,
        batch_sampler=BatchSamplers.NO_DUPLICATES,
        fp16=torch.cuda.is_available(),
        use_cpu=not torch.cuda.is_available(),
        save_strategy="no",
        report_to="none",
        seed=SEED,
    )

    trainer = SentenceTransformerTrainer(
        model=model,
        args=training_arguments,
        train_dataset=train_dataset,
        loss=loss,
    )

    trainer.train()

    model.save(str(output_folder))

    print(f"trained on {len(pairs)} pairs for {epochs} epochs, saved to {output_folder.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
