"""
Fine-tune a SQuAD 2.0 reader on our own examples from the train split.

The model reads a question and a passage, and predicts the start and end of the answer span.
Predicting the very first token (<s>) for both means "no answer".

No-answer examples: the train split has none, and a model that never sees one learns to always
answer. So every second training question is also paired with a random passage from a different
source document, where its answer cannot be. About a third of the examples are then no-answer,
close to the mix in SQuAD 2.0. These still use only real questions and real passages.

Long passages are cut into overlapping windows of 384 tokens. A window that shows only part of
an answer is skipped, so the model never learns that a half-visible answer means "no answer".

Training uses an NVIDIA GPU when there is one (like on Colab), and the CPU otherwise.

Run from the project root, after export_squad.py. Arguments are optional:
    python scripts/train_reader.py <base model> <share of training data> <epochs>
    python scripts/train_reader.py deepset/roberta-base-squad2 1.0 2

Saves the model to models/reader-<base model>-<percent>pct.
"""

import json
import random
import sys
from pathlib import Path
from typing import Any

import torch
from datasets import Dataset
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, Trainer, TrainingArguments

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.data_types import Passage, SquadExample  # noqa: E402
from src.passages import load_searchable_passages  # noqa: E402

TRAIN_FILE = PROJECT_ROOT / "data" / "squad" / "train.jsonl"

MODELS_FOLDER = PROJECT_ROOT / "models"

SEED = 13

MAX_LENGTH = 384

STRIDE = 128

BATCH_SIZE = 16

LEARNING_RATE = 3e-5


def read_examples() -> list[SquadExample]:
    with open(TRAIN_FILE, encoding="utf-8") as file:
        return [json.loads(line) for line in file]


def source_of(passage_id: str) -> str:
    return passage_id.rsplit("-", 1)[0]


def no_answer_copy(example: SquadExample, other_passage: Passage) -> SquadExample:
    return {
        "id": example["id"] + "::no-answer",
        "question": example["question"],
        "context": other_passage["text"],
        "answer_text": None,
        "answer_start": None,
        "passage_id": other_passage["passage_id"],
        "origin": "no_answer_rule",
        "level": example["level"],
        "style": other_passage["style"],
        "split": example["split"],
    }


def add_no_answer_examples(examples: list[SquadExample], rng: random.Random) -> list[SquadExample]:
    all_passages = load_searchable_passages()

    with_no_answer = list(examples)

    for position, example in enumerate(examples):
        if position % 2 != 0:
            continue

        own_source = source_of(example["passage_id"])

        other_passages = [p for p in all_passages if p["source_id"] != own_source]

        with_no_answer.append(no_answer_copy(example, rng.choice(other_passages)))

    return with_no_answer


def answer_tokens(example: SquadExample, offsets: list[tuple[int, int]], context_tokens: list[int]) -> tuple[int, int] | None:
    """Token positions of the answer in this window, (0, 0) for no answer, or None if it only partly fits."""
    if example["answer_text"] is None or example["answer_start"] is None:
        return 0, 0

    answer_start = example["answer_start"]

    answer_end = answer_start + len(example["answer_text"])

    window_start = offsets[context_tokens[0]][0]

    window_end = offsets[context_tokens[-1]][1]

    if window_start > answer_start or window_end < answer_end:
        return None

    start_token = next(t for t in context_tokens if offsets[t][1] > answer_start)

    end_token = next(t for t in reversed(context_tokens) if offsets[t][0] < answer_end)

    return start_token, end_token


def make_features(tokenizer: Any, examples: list[SquadExample]) -> dict[str, list[Any]]:
    encoded = tokenizer(
        [e["question"] for e in examples],
        [e["context"] for e in examples],
        truncation="only_second",
        max_length=MAX_LENGTH,
        stride=STRIDE,
        return_overflowing_tokens=True,
        return_offsets_mapping=True,
        padding="max_length",
    )

    features: dict[str, list[Any]] = {"input_ids": [], "attention_mask": [], "start_positions": [], "end_positions": []}

    for window, offsets in enumerate(encoded["offset_mapping"]):
        example = examples[encoded["overflow_to_sample_mapping"][window]]

        sequence_ids = encoded.sequence_ids(window)

        context_tokens = [token for token, sequence in enumerate(sequence_ids) if sequence == 1]

        positions = answer_tokens(example, offsets, context_tokens)

        if positions is None:
            continue

        features["input_ids"].append(encoded["input_ids"][window])

        features["attention_mask"].append(encoded["attention_mask"][window])

        features["start_positions"].append(positions[0])

        features["end_positions"].append(positions[1])

    return features


def main() -> None:
    base_model = sys.argv[1] if len(sys.argv) > 1 else "deepset/roberta-base-squad2"

    share = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0

    epochs = int(sys.argv[3]) if len(sys.argv) > 3 else 2

    short_name = base_model.rstrip("/").split("/")[-1]

    output_folder = MODELS_FOLDER / f"reader-{short_name}-{round(share * 100)}pct"

    rng = random.Random(SEED)

    examples = read_examples()

    rng.shuffle(examples)

    examples = examples[: round(len(examples) * share)]

    examples = add_no_answer_examples(examples, rng)

    tokenizer = AutoTokenizer.from_pretrained(base_model)

    features = make_features(tokenizer, examples)

    no_answer_windows = sum(1 for start in features["start_positions"] if start == 0)

    print(f"{len(examples)} examples became {len(features['input_ids'])} windows ({no_answer_windows} no-answer)")

    model = AutoModelForQuestionAnswering.from_pretrained(base_model)

    training_arguments = TrainingArguments(
        output_dir=str(MODELS_FOLDER / "checkpoints"),
        num_train_epochs=epochs,
        per_device_train_batch_size=BATCH_SIZE,
        learning_rate=LEARNING_RATE,
        weight_decay=0.01,
        warmup_ratio=0.1,
        fp16=torch.cuda.is_available(),
        use_cpu=not torch.cuda.is_available(),
        save_strategy="no",
        report_to="none",
        logging_steps=10,
        seed=SEED,
    )

    trainer = Trainer(model=model, args=training_arguments, train_dataset=Dataset.from_dict(features))

    trainer.train()

    trainer.save_model(str(output_folder))

    tokenizer.save_pretrained(str(output_folder))

    print(f"saved to {output_folder.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
