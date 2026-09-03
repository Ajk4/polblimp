# PolBLiMP

Polish Benchmark of Linguistic Minimal Pairs.

Generated minimal pairs are in [polblimp/output](polblimp/output).

## Setup

Requires Python 3 and Git LFS.

```sh
git lfs pull
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate data

Run generators from the `polblimp` directory:

```sh
cd polblimp

# Generate every paradigm
python generate.py --paradigm all

# Generate one paradigm
python generate.py --paradigm subj_verb_number_simple
```

## Developer guide

Query definitions are in each paradigm's `README.md`. Executable PML-TQ queries are in the adjacent `queries` directory.

Run all tests from the `polblimp` directory:

```sh
cd polblimp
python -m unittest discover tests
```

The tests have different purposes:

- `test_sentence_text.py` checks specific sentence transformations. Add cases here for errors found in generated pairs.
- `test_dataset_output_snapshots.py` checks that refactors do not change generated output. After an intentional output change, refresh its hashes from the repository root:

```sh
python polblimp/tests/refresh_snapshots.py
```

- `test_dataset_result_counts.py` checks local matcher counts against the remote PML-TQ search engine. After changing a query, refresh its counts from the repository root:

```sh
python polblimp/tests/refresh_queries_counts.py
```

The morphology dictionary is stored in Git LFS. Rebuild it only after changing its generator or the included PoliMorf source:

```sh
python polblimp/generate_morph_dict.py
```
