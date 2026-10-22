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

## Steps

1. **read**: Read your contact exports through the column map: one contact per key, phones and addresses attached.
2. **standardize**: Make names, phones and addresses comparable.
3. **find_candidates**: Pair the contacts worth comparing.
4. **compare**: Measure how alike the two contacts of each pair are.
5. **learn**: Score every pair from your reviews, and ask you about the pairs it is least sure of.
6. **decide**: Decide each pair: match, to review, or different.
7. **group**: Group matched contacts into entities, refusing merges decided different.
8. **publish**: Give every contact its entity id.

## Reference data

Shipped in `contacts_nayose/reference/`, as the studio used it: `towns.tsv`.
