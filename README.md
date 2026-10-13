# Ask My Pension

A question answering assistant for the Nigerian Contributory Pension Scheme.

A worker types a plain question such as "What is an RSA?" or "How do I move my
RSA to another PFA?" and gets a short answer taken from real pension documents,
the passage the answer came from, and simple explanations of any pension terms
in the answer.

The project is built for people with no finance background. Every design choice
is judged by one question: would a normal Nigerian worker understand this answer
on first read?

## Status

In development. Currently collecting and checking the source documents.

## Project links

- GitHub repository: this repo
- Live app: _not deployed yet_
- Demo video: _not recorded yet_
- Report: _not written yet_

## How the system works

The system has three stages.

1. **Retriever.** Given a question, find the passages most likely to hold the
   answer. Baseline is BM25. The improved version is a small sentence embedding
   model fine-tuned on our own question to passage pairs.
2. **Reader.** Given the question and the top passages, point at the exact answer
   span inside a passage, or say the passage has no answer. Baseline is an
   off-the-shelf SQuAD 2.0 model used with no extra training. The improved
   version is that model fine-tuned on our own annotated data.
3. **Plain language support.** Passages are tagged `plain` or `legal`. When both
   kinds answer the question, the system prefers the plain one. A glossary
   explains key terms under the answer.

Questions outside the pension domain get a polite refusal, not a guessed answer.

After the English system is finished and deployed, Igbo, Yoruba and Hausa are
added as a convenience feature using an existing translation model. That layer
is not trained and not evaluated by us.

## Repository layout

```
data/raw           untouched downloaded documents plus a manifest
data/processed     cleaned documents split into passages
data/annotations   question and answer pairs written by hand
data/splits        train, validation and test splits
data/glossary      pension terms and their simple explanations
src                reusable code
scripts            runnable steps (download, process, train, evaluate)
notebooks          training notebooks for Google Colab or Kaggle
app                the deployed web app
results            metrics, tables and figures
```

## How to run

Needs Python 3.10 or newer. Create a project environment and install the
dependencies:

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The versions in `requirements.txt` are chosen so the project runs the same on an
Intel Mac (where PyTorch stops at 2.2.2), on Google Colab and in a Codespace.

All code is type annotated. Check the types the way `tsc` would, with:

```
mypy src scripts
```

### 1. Get the source documents

The source documents belong to their publishers, so they are not stored in this
repository. The list of sources is in [data/sources.csv](data/sources.csv).
Download them with:

```
python scripts/download_sources.py
```

This saves every document, untouched, into `data/raw/`. Compare the checksums
against [data/raw/manifest.csv](data/raw/manifest.csv) to confirm you have the
same copies we used.

### 2. Build the passages

```
python scripts/build_passages.py
```

This cleans the documents and writes `data/processed/passages.jsonl`. FAQ answers
become one passage each, with their question kept next to them. Legal documents
become one passage per numbered clause, plus one per row of their definitions
tables. Every passage records its source, section, whether the source is `plain`
(written for ordinary workers) or `legal`, its Flesch Reading Ease score, and any
rates or naira amounts that may go out of date.

### 3. Stats and glossary suggestions

```
python scripts/passage_stats.py
python scripts/suggest_glossary_terms.py
```

The first writes [results/passage_stats.json](results/passage_stats.json). The
second counts the most common pension acronyms and phrases into
[data/glossary/term_candidates.csv](data/glossary/term_candidates.csv). The
glossary itself, [data/glossary/glossary.csv](data/glossary/glossary.csv), is
written by hand.

### 4. Freeze the train, validation and test split

```
python scripts/make_splits.py
```

Passages are split by section, never one by one, so questions about the same
section cannot appear in both training and test. The result,
[data/splits/sections.json](data/splits/sections.json), is committed and frozen
before any annotation is written.

### 5. Annotate

```
python scripts/make_review_files.py
python scripts/annotation_tool.py
```

The first creates the review files in `data/annotations/` and never overwrites
them. The second opens a local page for writing annotations, which are saved to
`data/annotations/annotations.jsonl` as passage IDs and answer positions. The
passage text is not stored, because it belongs to the publishers.

FAQ questions are not span-annotated by hand. The FAQ answers were written to answer
their questions directly, so each whole answer is used as the answer span, by rule.
Their beginner or detailed level is labelled by hand in `faq_levels.csv` for the test
and validation splits. Hand annotation focuses on what the FAQ cannot provide:
questions written the way workers ask them, questions about the legal passages, and
questions that a passage does not answer.

### 6. Evaluate the BM25 baseline retriever

```
python scripts/evaluate_bm25.py
```

BM25 ranks every searchable passage for each evaluation question: the FAQ questions,
whose gold passage is their own answer, and the hand-written questions. It reports
Recall@1, Recall@5 and MRR@10 on the validation and test splits, broken down by
question origin, source style and level, plus the reading ease of the top passage.
Results go to `results/bm25_results.json`, and every experiment adds a row to
[results/experiments.md](results/experiments.md).

### 7. Build the SQuAD files

```
python scripts/export_squad.py
```

Turns the FAQ pairs and the annotations into SQuAD 2.0 style examples in
`data/squad/` (one file per split). Each example records where it came from:
`faq_rule` (an FAQ question with its whole answer as the span), `faq_human`
(an FAQ question whose span was marked by hand) or `own` (a hand-written question).

### 8. Evaluate a dense retriever

```
python scripts/evaluate_dense.py BAAI/bge-small-en-v1.5
```

Scores a dense retriever exactly like BM25, so the numbers compare directly. It
takes an off-the-shelf model name or a fine-tuned model folder.

### 9. Evaluate a reader

```
python scripts/evaluate_reader.py deepset/roberta-base-squad2 bm25
```

The first argument is the reader (a model name or a fine-tuned folder), the second
is the retriever (`bm25`, or a dense model). The reader is scored with Exact Match
and F1 in two settings: given the gold passage (the reader alone), and end to end
on the retriever's top 3 passages (the whole system). It also measures the refusal
rate on the out-of-domain questions. The no-answer threshold is tuned on the
validation split and then applied unchanged to test.

### 10. Fine-tune on Google Colab

Open [notebooks/train_on_colab.ipynb](notebooks/train_on_colab.ipynb) in Colab with
a T4 GPU, upload `data/processed/passages.jsonl`, and run the cells in order. It
fine-tunes both retrievers (`scripts/train_retriever.py`) and both readers
(`scripts/train_reader.py`), evaluates every combination, repeats training on 25%,
50% and 75% of the data, and gives back `results.zip` to copy into `results/`.

The reader learns "no answer" from training questions paired with passages from
other documents. How those passages are chosen is itself an experiment. `random`
picks any passage, which taught the reader a shortcut: nearly every answerable
example was plain text and most no-answer passages were legal, so it learned that
legal text means "no answer". `matched` (the default) picks a passage of the same
style that shares at most one key word with the question, which removes the shortcut.

### 11. The plain-language preference experiment

```
python scripts/evaluate_plain_boost.py models/retriever-bge-small-en-v1.5-100pct models/reader-roberta-base-squad2-100pct-matched
```

Plain passages get a small boost before re-ranking, so they win close calls against
legal passages. The script sweeps several boost sizes and reports what each does to
retrieval (overall, FAQ, own, plain, legal), to end-to-end F1, and to readability.
The app's boost (0.02) is fixed by design rather than tuned, because the validation
split has no legal questions and so cannot show what a boost costs.

### 12. Error analysis

```
python scripts/error_analysis.py
```

Sorts every test question into one outcome (correct, retriever missed the gold
passage, gold passage read but the answer taken from another, wrong span, partly
right, refused when answerable, answered when it should have refused), with counts
by slice and real examples, in [results/error_analysis.md](results/error_analysis.md).
Because the documents overlap, an answer from a different passage can still be
right, so those cases go to `results/manual_review.csv` to be checked by hand.

### 13. Run the app

```
streamlit run app/streamlit_app.py
```

The app answers with the same models and settings as the experiments: the fine-tuned
bge retriever, the 0.02 plain boost, the top 3 passages, the fine-tuned reader and the
no-answer threshold tuned on validation. It shows the answer first, simple
explanations of any glossary terms in it, and the passage and document it came from.
If no answer clears the threshold, it politely refuses. The first start embeds every
passage and saves the result to `models/passage_embeddings.npy`, so later starts are
quick. On a laptop CPU an answer takes under two seconds, and the app uses about
800 MB of memory.

### 14. Deploy on Streamlit Community Cloud

The models (about 620 MB) cannot go in git, and the passages hold the publishers'
text, so both live in a private Hugging Face model repository that the app downloads
from on its first start.

```
python scripts/prepare_assets.py
hf auth login
hf upload michael-alu/ask-my-pension-assets assets . --private
```

Then create the app on [Streamlit Community Cloud](https://share.streamlit.io) from
this GitHub repository, with `app/streamlit_app.py` as the main file and Python 3.10
or newer. Under Advanced settings, add two secrets:

```
HF_ASSETS_REPO = "michael-alu/ask-my-pension-assets"
HF_TOKEN = "<a Hugging Face token that can read it>"
```

The app's own dependencies are in `app/requirements.txt`, which uses the CPU-only
build of PyTorch to keep the install small.

## Dataset

_Not written yet._

## Experiments and results

_Not written yet._

## Acknowledgements and licensing

The full list of documents, models, libraries and papers used, with sources and
licences, is in the project report.

This is a student project. It is not official financial or legal advice, and it
is not connected to or endorsed by PenCom or any pension fund administrator.
