# PolBLiMP

Polish Benchmark of Linguistic Minimal Pairs. Generated datasets are in
[polblimp/output](polblimp/output).

## Setup

Requires Python 3 and Git LFS.

```sh
git lfs pull
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Generate

Run generators from `polblimp/`:

```sh
cd polblimp
python generate.py --paradigm all
python generate.py --paradigm subj_verb_number_simple
```

## Paradigms

Phenomena form a hierarchy under `polblimp/phenomena/`. Example:

```text
subject_predicate_agreement/verb/number/subj_verb_number_simple/
```

Each paradigm contains:

- `README.md`: linguistic definition, examples, and source queries.
- `queries/*.pmltq`: query variants of the source queries.
- `generator.py`: local query implementations and sentence transformations.

Shared code belongs in the nearest `common.py` in the hierarchy.

*.pmltq files are used by tests to assert that local implementation matches external results (see https://lindat.mff.cuni.cz/services/pmltq/?query=pdb)
NOTE that those could be used for directly fetching connlu from lindat API instead of reimplementing it locally.
This is reasonable next improvement to the project. POC is available on api-queries git branch.

## How to add new paradigm

1. Add the paradigm `README.md` and executable query variants.
2. Implement equivalent local matchers in `generator.py`.
3. Implement transformations and register the generator in `generate.py`.
4. Register matchers in `test_dataset_result_counts.py` and query paths in `refresh_queries_counts.py`.

The count test compares local matcher counts with PML-TQ results stored in `dataset_result_counts.json`. PML-TQ counts every match path, while generation uses one match per sentence and query variant.

Refresh counts from the repository root after changing queries:

```sh
python polblimp/tests/refresh_queries_counts.py
```

## Snapshot test

`test_dataset_output_snapshots.py` asserts that complete generated outputs have not changed. Use it when refactoring code that should preserve behavior.

Refresh snapshots only after reviewing an intentional output change:

```sh
python polblimp/tests/refresh_snapshots.py
```

## Sentence test

`test_sentence_text.py` checks exact transformations of selected corpus sentences. Useful when some incorrect sentence transformation is found.

## Tests

Run all tests from `polblimp/`:

```sh
cd polblimp
python -m unittest discover tests
```

## Morphology dictionary

We process PoliMorf into .csv file with filtered out morphologic data we need in PolBLiMP transforms. 

After changes to `polblimp/generate_morph_dict.py` make sure to run and commit updated dictionary file to the repo.
