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

_Later steps not written yet._

## Dataset

_Not written yet._

## Experiments and results

_Not written yet._

## Acknowledgements and licensing

The full list of documents, models, libraries and papers used, with sources and
licences, is in the project report.

This is a student project. It is not official financial or legal advice, and it
is not connected to or endorsed by PenCom or any pension fund administrator.
