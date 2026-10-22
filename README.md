# Contact matching

Give every contact one entity id: contacts of the same person or company share it, and uncertain pairs go to you.

Exported from Agent Workflow Studio (release 1.0.0 of the workflow API `contacts-nayose`). It is the same
logic the studio runs (`contacts_nayose/core/`), without ComfyUI. Regenerate it from the studio rather than
editing `contacts_nayose/pipeline.py`.

## Install and run

```bash
pip install .                          # or the wheel the studio built
contacts-nayose init                    # config.yaml: every input, described, to edit
contacts-nayose run --config config.yaml --out out
contacts-nayose check                   # the examples and every stage Check
```

The same commands work on Windows, macOS and Linux (Python 3.12 or later; on Windows, in
PowerShell or cmd, with `py -m pip install .`).

Results go to `out/`: `entities`, `review_queue`. When the workflow asks you to review pairs, it writes
`out/review_batch.csv`: fill its `decision` column (same / different), then run again with
`--reviews out/review_batch.csv`. Every decision so far is kept in `out/reviews.csv`.

## Inputs

| Option | What it is | Default |
|---|---|---|
| `--exports` | The folder with your contact exports (contacts, phones and addresses CSV files). | `sample` |
| `--columns` | The column map: which column of your exports holds the key, names, birth date, phones and addresses. | in config.yaml (`init` writes it) |
| `--batch` | How many pairs to ask you about each run. | `50` |
| `--match-at` | Merge pairs at least this likely to be the same (raise it for fewer wrong merges). | `0.5` |
| `--review-from` | Pairs from here up to Match at go to your review queue. | `0.1` |
| `--corroboration` | A merge also needs a shared phone, house, town or alias, not only name and birth date. | `False` |
| `--max-size` | The most contacts one entity may have. | `12` |

## More commands

### `contacts-nayose benchmark`

Measure contact matching on generated contacts with an answer key: the same stages as Contact matching, with a reviewer who knows the answers.

| Option | What it is | Default |
|---|---|---|
| `--profile` | How dirty, and with real names and companies or not (real and company profiles need the public sources downloaded once). | `company_hard` |
| `--contacts` | About how many contacts to generate. | `10000` |
| `--seed` | The same seed gives the same data. | `7` |
| `--budget` | How many reviews the simulated reviewer makes (about 1,000 for a good model). | `1000` |
| `--out` | Where its results and run folders go | `benchmark` |

### `contacts-nayose generate`

Generate CRM-shaped contacts with realistic dirt and their answer key, to try or measure contact matching.

| Option | What it is | Default |
|---|---|---|
| `--profile` | How dirty, and with real names and companies or not (real and company profiles need the public sources downloaded once). | `company_hard` |
| `--contacts` | About how many contacts to generate. | `10000` |
| `--seed` | The same seed gives the same data. | `7` |
| `--out` | Where its results and run folders go | `generate` |


## Steps

1. **read**: Read your contact exports through the column map: one contact per key, phones and addresses attached.
2. **standardize**: Make names, phones and addresses comparable.
3. **find_candidates**: Pair the contacts worth comparing.
4. **compare**: Measure how alike the two contacts of each pair are.
5. **learn**: Score every pair from your reviews, and ask you about the pairs it is least sure of.
6. **decide**: Decide each pair: match, to review, or different.
7. **group**: Group matched contacts into entities, refusing merges decided different.
8. **publish**: Give every contact its entity id.

## Decisions

- **A model learns the weights from your reviews (logistic regression, active learning).** It beat fixed rules, Fellegi–Sunter and gradient boosting in every trial. Instead of: hand-set points.
- **No embeddings or reranker.** Neither improved the result at 100,000 contacts (research/contacts_er/RESULTS.md). Instead of: a dense index and a cross-encoder.
- **Uncertain pairs and disputed reviews go to you.** A wrong merge costs more than a question. Instead of: auto-deciding everything.
- **Its quality comes from your reviews: about 1,000 make it good. Review a round, run again; a larger round (reviews per round 200) means fewer runs.** Measured on the hard 10k benchmark: no reviews F1 0.54 (precision 0.85, recall 0.39); 1,000 reviews F1 0.96 (precision 0.99, recall 0.94). Instead of: fixed weights tuned on synthetic data, which would not fit yours.

## Optional: real-data

`pip install ".[real-data]"`, then `python -m contacts_nayose.nayose_bench.sources` downloads the public data the real and company profiles use, once: real names (NVIDIA Nemotron-Personas-Japan, CC BY 4.0), readings (UniDic, JMnedict: share-alike), towns (Japan Post) and companies (National Tax Agency corporate numbers: 出典：国税庁法人番号公表サイト). Their licences apply; nothing is shipped with this package.

## Reference data

Shipped in `contacts_nayose/reference/`, as the studio used it: `towns.tsv`.
