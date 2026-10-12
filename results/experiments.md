# Experiments

| experiment | split | questions | recall_at_1 | recall_at_5 | mrr_at_10 | exact_match | f1 | ood_refusal_rate | top1_reading_ease | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| BM25 retriever (baseline) | validation | 71 | 0.239 | 0.549 | 0.358 |  |  |  | 40.7 |  |
| BM25 retriever (baseline) | test | 125 | 0.28 | 0.464 | 0.354 |  |  |  | 26.8 |  |
| Dense retriever bge-small-en-v1.5 (zero-shot) | validation | 71 | 0.366 | 0.789 | 0.539 |  |  |  | 46.1 |  |
| Dense retriever bge-small-en-v1.5 (zero-shot) | test | 125 | 0.352 | 0.568 | 0.442 |  |  |  | 34.8 |  |
| Dense retriever retriever-bge-small-en-v1.5-100pct | validation | 71 | 0.465 | 0.831 | 0.631 |  |  |  | 44.1 |  |
| Dense retriever retriever-bge-small-en-v1.5-100pct | test | 125 | 0.456 | 0.704 | 0.558 |  |  |  | 33.3 |  |
| Dense retriever all-MiniLM-L6-v2 (zero-shot) | validation | 71 | 0.352 | 0.775 | 0.529 |  |  |  | 40.3 |  |
| Dense retriever all-MiniLM-L6-v2 (zero-shot) | test | 125 | 0.28 | 0.496 | 0.378 |  |  |  | 37.3 |  |
| Dense retriever retriever-all-MiniLM-L6-v2-100pct | validation | 71 | 0.408 | 0.845 | 0.592 |  |  |  | 38.7 |  |
| Dense retriever retriever-all-MiniLM-L6-v2-100pct | test | 125 | 0.416 | 0.648 | 0.511 |  |  |  | 35.3 |  |
| BM25 + reader roberta-base-squad2 (zero-shot), end to end | test | 134 |  |  |  | 0.015 | 0.19 | 0.578 | 30.3 | threshold -0.8 (tuned on validation); answerable F1 0.196, no-answer accuracy 0.111; at threshold 0: F1 0.178, OOD refusal 0.867 |
| bge-small-en-v1.5 (zero-shot) + reader roberta-base-squad2 (zero-shot), end to end | test | 134 |  |  |  | 0.007 | 0.19 | 0.422 | 36.1 | threshold -0.8 (tuned on validation); answerable F1 0.196, no-answer accuracy 0.111; at threshold 0: F1 0.183, OOD refusal 0.8 |
| Reader roberta-base-squad2 (zero-shot), gold passage | test | 134 |  |  |  | 0.06 | 0.403 |  |  | threshold -0.8 (tuned on validation); answerable F1 0.4, no-answer accuracy 0.444 |
| retriever-bge-small-en-v1.5-100pct + reader roberta-base-squad2 (zero-shot), end to end | test | 134 |  |  |  | 0.022 | 0.212 | 0.333 | 33.0 | threshold -0.8 (tuned on validation); answerable F1 0.219, no-answer accuracy 0.111; at threshold 0: F1 0.208, OOD refusal 0.733 |
| BM25 + reader reader-roberta-base-squad2-100pct-random, end to end | test | 134 |  |  |  | 0.179 | 0.339 | 0.6 | 34.1 | threshold 0.0 (tuned on validation); answerable F1 0.339, no-answer accuracy 0.333; at threshold 0: F1 0.339, OOD refusal 0.6 |
| Reader reader-roberta-base-squad2-100pct-random, gold passage | test | 134 |  |  |  | 0.575 | 0.747 |  |  | threshold 0.0 (tuned on validation); answerable F1 0.736, no-answer accuracy 0.889 |
| retriever-bge-small-en-v1.5-100pct + reader reader-roberta-base-squad2-100pct-random, end to end | test | 134 |  |  |  | 0.179 | 0.358 | 0.356 | 30.6 | threshold 0.0 (tuned on validation); answerable F1 0.384, no-answer accuracy 0.0; at threshold 0: F1 0.358, OOD refusal 0.356 |
| Reader tinyroberta-squad2 (zero-shot), gold passage | test | 134 |  |  |  | 0.045 | 0.376 |  |  | threshold -1.0 (tuned on validation); answerable F1 0.403, no-answer accuracy 0.0 |
| BM25 + reader tinyroberta-squad2 (zero-shot), end to end | test | 134 |  |  |  | 0.022 | 0.19 | 0.0 | 31.0 | threshold -1.0 (tuned on validation); answerable F1 0.204, no-answer accuracy 0.0; at threshold 0: F1 0.124, OOD refusal 0.822 |
| Reader reader-tinyroberta-squad2-100pct-random, gold passage | test | 134 |  |  |  | 0.806 | 0.855 |  |  | threshold -0.85 (tuned on validation); answerable F1 0.861, no-answer accuracy 0.778 |
| retriever-bge-small-en-v1.5-100pct + reader reader-tinyroberta-squad2-100pct-random, end to end | test | 134 |  |  |  | 0.381 | 0.51 | 0.4 | 34.0 | threshold -0.85 (tuned on validation); answerable F1 0.546, no-answer accuracy 0.0; at threshold 0: F1 0.515, OOD refusal 0.511 |
| Dense retriever retriever-bge-small-en-v1.5-25pct | validation | 71 | 0.423 | 0.817 | 0.583 |  |  |  | 45.9 |  |
| Dense retriever retriever-bge-small-en-v1.5-25pct | test | 125 | 0.384 | 0.624 | 0.493 |  |  |  | 33.8 |  |
| Reader reader-roberta-base-squad2-25pct-random, gold passage | test | 134 |  |  |  | 0.552 | 0.79 |  |  | threshold -0.45 (tuned on validation); answerable F1 0.807, no-answer accuracy 0.556 |
| BM25 + reader reader-roberta-base-squad2-25pct-random, end to end | test | 134 |  |  |  | 0.194 | 0.371 | 0.533 | 33.2 | threshold -0.45 (tuned on validation); answerable F1 0.389, no-answer accuracy 0.111; at threshold 0: F1 0.359, OOD refusal 0.8 |
| Dense retriever retriever-bge-small-en-v1.5-50pct | validation | 71 | 0.437 | 0.831 | 0.603 |  |  |  | 45.5 |  |
| Dense retriever retriever-bge-small-en-v1.5-50pct | test | 125 | 0.408 | 0.664 | 0.515 |  |  |  | 34.8 |  |
| Reader reader-roberta-base-squad2-50pct-random, gold passage | test | 134 |  |  |  | 0.56 | 0.786 |  |  | threshold 0.0 (tuned on validation); answerable F1 0.795, no-answer accuracy 0.667 |
| BM25 + reader reader-roberta-base-squad2-50pct-random, end to end | test | 134 |  |  |  | 0.149 | 0.31 | 0.578 | 35.4 | threshold 0.0 (tuned on validation); answerable F1 0.324, no-answer accuracy 0.111; at threshold 0: F1 0.31, OOD refusal 0.578 |
| Dense retriever retriever-bge-small-en-v1.5-75pct | validation | 71 | 0.465 | 0.817 | 0.625 |  |  |  | 45.3 |  |
| Dense retriever retriever-bge-small-en-v1.5-75pct | test | 125 | 0.44 | 0.68 | 0.547 |  |  |  | 34.3 |  |
| Reader reader-roberta-base-squad2-75pct-random, gold passage | test | 134 |  |  |  | 0.59 | 0.768 |  |  | threshold 0.0 (tuned on validation); answerable F1 0.759, no-answer accuracy 0.889 |
| BM25 + reader reader-roberta-base-squad2-75pct-random, end to end | test | 134 |  |  |  | 0.187 | 0.35 | 0.778 | 34.6 | threshold 0.0 (tuned on validation); answerable F1 0.359, no-answer accuracy 0.222; at threshold 0: F1 0.35, OOD refusal 0.778 |
| Reader reader-roberta-base-squad2-100pct-matched, gold passage | test | 134 |  |  |  | 0.53 | 0.762 |  |  | threshold -0.75 (tuned on validation); answerable F1 0.768, no-answer accuracy 0.667 |
| BM25 + reader reader-roberta-base-squad2-100pct-matched, end to end | test | 134 |  |  |  | 0.224 | 0.379 | 0.689 | 34.1 | threshold -0.75 (tuned on validation); answerable F1 0.382, no-answer accuracy 0.333; at threshold 0: F1 0.36, OOD refusal 0.867 |
