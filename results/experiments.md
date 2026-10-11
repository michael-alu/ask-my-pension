# Experiments

| experiment | split | questions | recall_at_1 | recall_at_5 | mrr_at_10 | exact_match | f1 | ood_refusal_rate | top1_reading_ease | notes |
|---|---|---|---|---|---|---|---|---|---|---|
| BM25 retriever (baseline) | validation | 71 | 0.239 | 0.549 | 0.358 |  |  |  | 40.7 |  |
| BM25 retriever (baseline) | test | 125 | 0.28 | 0.464 | 0.354 |  |  |  | 26.8 |  |
| bge-small-en-v1.5 (zero-shot) + reader roberta-base-squad2 (zero-shot), end to end | test | 134 |  |  |  | 0.007 | 0.157 | 0.422 | 35.6 | threshold -0.8 (tuned on validation); answerable F1 0.16, no-answer accuracy 0.111; at threshold 0: F1 0.153, OOD refusal 0.8 |
| Reader roberta-base-squad2 (zero-shot), gold passage | test | 134 |  |  |  | 0.06 | 0.403 |  |  | threshold -0.8 (tuned on validation); answerable F1 0.4, no-answer accuracy 0.444 |
| BM25 + reader roberta-base-squad2 (zero-shot), end to end | test | 134 |  |  |  | 0.015 | 0.19 | 0.578 | 30.3 | threshold -0.8 (tuned on validation); answerable F1 0.196, no-answer accuracy 0.111; at threshold 0: F1 0.178, OOD refusal 0.867 |
| Reader reader-roberta-base-squad2-100pct, gold passage | test | 134 |  |  |  | 0.537 | 0.704 |  |  | threshold 0.15 (tuned on validation); answerable F1 0.691, no-answer accuracy 0.889 |
| BM25 + reader reader-roberta-base-squad2-100pct, end to end | test | 134 |  |  |  | 0.149 | 0.309 | 0.689 | 35.5 | threshold 0.15 (tuned on validation); answerable F1 0.307, no-answer accuracy 0.333; at threshold 0: F1 0.309, OOD refusal 0.689 |
