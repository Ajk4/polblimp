from __future__ import annotations

# Fetch the first sentence matched by a PML-TQ query as basic CoNLL-U.
#
# Example:
# python polblimp/tests/fetch_query_conllu_poc.py \
#   polblimp/phenomena/subject_predicate_agreement/verb/number/subj_verb_number_genitive/queries/1a.pmltq

import argparse
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT))

from phenomena.pmltq import fetch_trees, query_rows  # noqa: E402


def fetch_first_tree(query: str, treebank: str, timeout: int) -> tuple[str, int, str, list[list[object]]]:
    matches = query_rows(
        f"{query.rstrip()}\n>> file($root), tree_no($root), $root.id",
        treebank,
        timeout,
        1,
    )
    if not matches:
        raise RuntimeError("Query returned no matches")

    filename, tree_number, match_id = matches[0]
    tree = fetch_trees(treebank, {(str(filename), int(tree_number))})[(str(filename), int(tree_number))]
    rows = [
        [
            token["id"], token["form"], token["lemma"], token["upos"], token["xpos"],
            "|".join(f"{name}={value}" for name, value in (token["feats"] or {}).items()),
            token["head"], token["deprel"], (token["misc"] or {}).get("SpaceAfter") == "No",
        ]
        for token in tree
    ]
    return str(filename), int(tree_number), str(match_id), rows


def format_conllu(filename: str, tree_number: int, match_id: str, rows: list[list[object]]) -> str:
    lines = [
        f"# source = {filename}",
        f"# tree_number = {tree_number}",
        f"# match_id = {match_id}",
    ]
    for token_id, form, lemma, upos, xpos, feats, head, deprel, no_space_after in rows:
        misc = "SpaceAfter=No" if no_space_after else "_"
        columns = (token_id, form, lemma, upos, xpos, feats or "_", head, deprel, "_", misc)
        lines.append("\t".join(str(value) for value in columns))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch the first PML-TQ match as basic CoNLL-U.")
    parser.add_argument("query_file", type=Path)
    parser.add_argument("--treebank", choices=("lfg", "pdb"), default="lfg")
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    query = args.query_file.read_text()
    if ">>" in query:
        parser.error("query must not contain output filters")

    filename, tree_number, match_id, rows = fetch_first_tree(query, args.treebank, args.timeout)
    print(format_conllu(filename, tree_number, match_id, rows), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
