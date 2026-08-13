from __future__ import annotations

# Use this tool to get reference numbers of results from lindat.mff.cuni.cz search engine
#
# This is useful for automated testing of correctness of local matchers against remote queries.
#
# Examples:
# python polblimp/tests/refresh_queries_counts.py

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://lindat.mff.cuni.cz/services/pmltq/api/treebanks/{treebank}/query"
TREEBANKS = {
    "lfg": "udpl_lfg218",
    "pdb": "udpl_pdb218",
}
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
COUNTS_PATH = PACKAGE_ROOT / "tests" / "dataset_result_counts.json"
DATASET_ORDER = ("lfg", "pdb")

QUERY_FILES = {
    "match_subj_adjectival_gender": "adjective/adjective_only/subj_adjectival_gender/queries/1a.pmltq",
    "match_subj_adjectival_gender_cop": "adjective/adjective_and_copula/subj_adjectival_gender_cop/queries/1a.pmltq",
    "match_subj_adjectival_number_cop": "adjective/adjective_and_copula/subj_adjectival_number_cop/queries/1a.pmltq",
    "match_subj_verb_gender_simple_1a": "verb/gender/subj_verb_gender_simple/queries/1a.pmltq",
    "match_subj_verb_gender_simple_1b": "verb/gender/subj_verb_gender_simple/queries/1b.pmltq",
    "match_subj_verb_gender_simple_1c": "verb/gender/subj_verb_gender_simple/queries/1c.pmltq",
    "match_subj_verb_gender_simple_2a": "verb/gender/subj_verb_gender_simple/queries/2a.pmltq",
    "match_subj_verb_gender_simple_2b": "verb/gender/subj_verb_gender_simple/queries/2b.pmltq",
    "match_subj_verb_gender_simple_2c": "verb/gender/subj_verb_gender_simple/queries/2c.pmltq",
    "match_subj_verb_gender_genitive_1a": "verb/gender/subj_verb_gender_genitive/queries/1a.pmltq",
    "match_subj_verb_gender_csubj_1a": "verb/gender/subj_verb_gender_csubj/queries/1a.pmltq",
    "match_subj_verb_gender_csubj_2a": "verb/gender/subj_verb_gender_csubj/queries/2a.pmltq",
    "match_subj_verb_gender_numerals_1a": "verb/gender/subj_verb_gender_numerals/queries/1a.pmltq",
    "match_subj_verb_gender_numerals_2a": "verb/gender/subj_verb_gender_numerals/queries/2a.pmltq",
    "match_subj_verb_gender_attractor_1a": "verb/gender/subj_verb_gender_attractor/queries/1a.pmltq",
    "match_subj_verb_gender_attractor_1b": "verb/gender/subj_verb_gender_attractor/queries/1b.pmltq",
    "match_subj_verb_gender_attractor_1c": "verb/gender/subj_verb_gender_attractor/queries/1c.pmltq",
    "match_subj_verb_gender_attractor_2a": "verb/gender/subj_verb_gender_attractor/queries/2a.pmltq",
    "match_subj_verb_gender_attractor_2b": "verb/gender/subj_verb_gender_attractor/queries/2b.pmltq",
    "match_subj_verb_gender_attractor_2c": "verb/gender/subj_verb_gender_attractor/queries/2c.pmltq",
    "match_subj_verb_number_simple_1a": "verb/number/subj_verb_number_simple/queries/1a.pmltq",
    "match_subj_verb_number_simple_1b": "verb/number/subj_verb_number_simple/queries/1b.pmltq",
    "match_subj_verb_number_simple_1c": "verb/number/subj_verb_number_simple/queries/1c.pmltq",
    "match_subj_verb_number_simple_2a": "verb/number/subj_verb_number_simple/queries/2a.pmltq",
    "match_subj_verb_number_simple_2b": "verb/number/subj_verb_number_simple/queries/2b.pmltq",
    "match_subj_verb_number_simple_3a": "verb/number/subj_verb_number_simple/queries/3a.pmltq",
    "match_subj_verb_number_simple_3b": "verb/number/subj_verb_number_simple/queries/3b.pmltq",
    "match_subj_verb_number_genitive_1a": "verb/number/subj_verb_number_genitive/queries/1a.pmltq",
    "match_subj_verb_number_csubj_1a": "verb/number/subj_verb_number_csubj/queries/1a.pmltq",
    "match_subj_verb_number_csubj_2a": "verb/number/subj_verb_number_csubj/queries/2a.pmltq",
    "match_subj_verb_number_attractor_1a": "verb/number/subj_verb_number_attractor/queries/1a.pmltq",
    "match_subj_verb_number_attractor_1b": "verb/number/subj_verb_number_attractor/queries/1b.pmltq",
    "match_subj_verb_number_attractor_1c": "verb/number/subj_verb_number_attractor/queries/1c.pmltq",
    "match_subj_verb_number_attractor_2a": "verb/number/subj_verb_number_attractor/queries/2a.pmltq",
    "match_subj_verb_number_attractor_2b": "verb/number/subj_verb_number_attractor/queries/2b.pmltq",
    "match_subj_verb_number_attractor_3a": "verb/number/subj_verb_number_attractor/queries/3a.pmltq",
    "match_subj_verb_number_numerals_1a": "verb/number/subj_verb_number_numerals/queries/1a.pmltq",
    "match_subj_verb_number_numerals_1b": "verb/number/subj_verb_number_numerals/queries/1b.pmltq",
    "match_subj_verb_number_numerals_1c": "verb/number/subj_verb_number_numerals/queries/1c.pmltq",
    "match_subj_verb_number_numerals_2a": "verb/number/subj_verb_number_numerals/queries/2a.pmltq",
    "match_subj_verb_person_simple_1a": "verb/person/subj_verb_person_simple/queries/1a.pmltq",
    "match_subj_verb_person_simple_1b": "verb/person/subj_verb_person_simple/queries/1b.pmltq",
    "match_subj_verb_person_simple_1c": "verb/person/subj_verb_person_simple/queries/1c.pmltq",
    "match_subj_verb_person_simple_1d": "verb/person/subj_verb_person_simple/queries/1d.pmltq",
    "match_subj_verb_person_simple_2a": "verb/person/subj_verb_person_simple/queries/2a.pmltq",
    "match_subj_verb_person_simple_2b": "verb/person/subj_verb_person_simple/queries/2b.pmltq",
    "match_subj_verb_person_simple_2c": "verb/person/subj_verb_person_simple/queries/2c.pmltq",
    "match_subj_verb_person_numerals_1a": "verb/person/subj_verb_person_numerals/queries/1a.pmltq",
    "match_subj_verb_person_numerals_1b": "verb/person/subj_verb_person_numerals/queries/1b.pmltq",
    "match_subj_verb_person_numerals_1c": "verb/person/subj_verb_person_numerals/queries/1c.pmltq",
    "match_subj_verb_person_numerals_2a": "verb/person/subj_verb_person_numerals/queries/2a.pmltq",
    "match_subj_verb_person_numerals_2b": "verb/person/subj_verb_person_numerals/queries/2b.pmltq",
    "match_subj_verb_person_genitive_1a": "verb/person/subj_verb_person_genitive/queries/1a.pmltq",
    "match_subj_verb_person_genitive_1b": "verb/person/subj_verb_person_genitive/queries/1b.pmltq",
}

ALIASES = {
    "match_subj_adjectival_case": "match_subj_adjectival_number_cop",
    "match_subj_adjectival_number": "match_subj_adjectival_number_cop",
    "match_subj_verb_person_csubj_1a": "match_subj_verb_number_csubj_1a",
    "match_subj_verb_person_csubj_2a": "match_subj_verb_number_csubj_2a",
}


def query_count(query: str, treebank: str, timeout: int) -> int:
    payload = json.dumps({
        "query": f"{query.rstrip()}\n>> count()",
        "filter": True,
        "timeout": timeout,
        "limit": 1,
    }).encode()
    request = urllib.request.Request(
        API_URL.format(treebank=treebank),
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout + 10) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        message = error.read().decode(errors="replace")
        raise RuntimeError(f"PML-TQ returned HTTP {error.code}: {message}") from error

    try:
        return int(result["results"][0][0])
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise RuntimeError(f"Unexpected PML-TQ response: {result}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Update reference PML-TQ query counts.")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--output", type=Path, default=COUNTS_PATH)
    args = parser.parse_args()

    phenomena_dir = PACKAGE_ROOT / "phenomena" / "subject_predicate_agreement"
    queries = {
        name: (phenomena_dir / path).read_text()
        for name, path in QUERY_FILES.items()
    }
    for name, query in queries.items():
        if not query.strip():
            parser.error(f"query {name!r} is empty")
        if ">>" in query:
            parser.error(f"query {name!r} must not contain output filters")

    treebanks = TREEBANKS.items()
    counts: dict[str, dict[str, int]] = {name: {} for name in queries}
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = {
            executor.submit(query_count, query, treebank, args.timeout): (query_name, dataset)
            for query_name, query in queries.items()
            for dataset, treebank in treebanks
        }
        for future in as_completed(futures):
            query_name, dataset = futures[future]
            counts[query_name][dataset] = future.result()
            print(f"{query_name}: {dataset}={counts[query_name][dataset]}", flush=True)

    print()
    for matcher_name in queries:
        values = ", ".join(
            f"{dataset}={counts[matcher_name][dataset]}"
            for dataset, _ in treebanks
        )
        print(f"{matcher_name}: {values}")

    expected = {
        name: [dataset_counts[dataset] for dataset in DATASET_ORDER]
        for name, dataset_counts in counts.items()
    }
    expected.update(ALIASES)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(expected, indent=2) + "\n")
    print(f"Updated {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
