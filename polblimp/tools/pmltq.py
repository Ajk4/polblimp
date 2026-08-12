from __future__ import annotations

# Use this tool to get reference numbers of results from lindat.mff.cuni.cz search engine
#
# This is useful for automated testing of correctness of local matchers against remote queries.
#
# Examples:
# python polblimp/tools/pmltq.py \
#   polblimp/phenomena/subject_predicate_agreement/verb/number/subj_verb_number_simple/queries/*.pmltq
# python polblimp/tools/pmltq.py \
#   polblimp/phenomena/subject_predicate_agreement/verb/number/subj_verb_number_simple/queries/1a.pmltq \
#   --treebank lfg

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "https://lindat.mff.cuni.cz/services/pmltq/api/treebanks/{treebank}/query"
TREEBANKS = {
    "lfg": "udpl_lfg218",
    "pdb": "udpl_pdb218",
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
    parser = argparse.ArgumentParser(description="Count PML-TQ query matches.")
    parser.add_argument("query_files", type=Path, nargs="*", help="Read queries from these files; stdin by default.")
    parser.add_argument("--treebank", choices=["lfg", "pdb", "all"], default="all")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()

    queries = (
        {path.stem: path.read_text() for path in args.query_files}
        if args.query_files
        else {"stdin": sys.stdin.read()}
    )
    for name, query in queries.items():
        if not query.strip():
            parser.error(f"query {name!r} is empty")
        if ">>" in query:
            parser.error(f"query {name!r} must not contain output filters")

    treebanks = (
        TREEBANKS.items()
        if args.treebank == "all"
        else [(args.treebank, TREEBANKS[args.treebank])]
    )
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
    for query_name in queries:
        values = ", ".join(
            f"{dataset}={counts[query_name][dataset]}"
            for dataset, _ in treebanks
        )
        print(f"{query_name}: {values}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
