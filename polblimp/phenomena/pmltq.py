from __future__ import annotations

import json
import random
import re
import urllib.error
import urllib.request
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Callable, Optional

import conllu
import pandas as pd
from conllu import Token, TokenTree

from phenomena.common import sentence_text, token_trees


API_URL = "https://lindat.mff.cuni.cz/services/pmltq/api/treebanks/{treebank}/query"
TREEBANKS = {
    "lfg": "udpl_lfg218",
    "pdb": "udpl_pdb218",
}
TOKEN_COLUMNS = (
    "file($token), tree_no($token), $token.ord, $token.form, $token.lemma, "
    "$token.conll/cpos, $token.conll/pos, $token.conll/feat, {head}, "
    "$token.conll/deprel, $token.no_space_after"
)


Match = dict[str, Token | TokenTree]
Transform = Callable[[conllu.TokenList, Match], bool]


@dataclass(frozen=True)
class QueryVariant:
    query_name: str
    nodes: tuple[str, ...]
    transform: Transform
    seed_namespace: str


def query_rows(query: str, treebank: str, timeout: int = 120, limit: int = 100000) -> list[list[object]]:
    return [list(row) for row in _query_rows(query, treebank, timeout, limit)]


@lru_cache(maxsize=None)
def _query_rows(query: str, treebank: str, timeout: int, limit: int) -> tuple[tuple[object, ...], ...]:
    payload = json.dumps({
        "query": query,
        "filter": True,
        "timeout": timeout,
        "limit": limit,
    }).encode()
    request = urllib.request.Request(
        API_URL.format(treebank=TREEBANKS[treebank]),
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

    if "results" not in result:
        raise RuntimeError(f"Unexpected PML-TQ response: {result}")
    return tuple(tuple(row) for row in result["results"])


def run_query_transforms(
        sentences: list[conllu.TokenList],
        queries_dir: Path,
        variants: tuple[QueryVariant, ...],
        limit: Optional[int],
) -> pd.DataFrame:
    sentences_by_id = {
        (str(sentence.metadata["dataset"]), str(sentence.metadata["sent_id"])): (index, sentence)
        for index, sentence in enumerate(sentences)
    }
    treebanks = _treebanks_for_sentences(sentences)
    frames = []

    for variant in variants:
        query = (queries_dir / f"{variant.query_name}.pmltq").read_text()
        output_columns = ", ".join(["$root.id", "$root.ord", *(f"${node}.ord" for node in variant.nodes)])
        api_matches = []
        for treebank in treebanks:
            api_matches.extend(
                (treebank, match)
                for match in query_rows(f"{query.rstrip()}\n>> {output_columns}", treebank)
            )

        matches_by_index: dict[int, tuple[conllu.TokenList, object, list[object]]] = {}
        for treebank, (root_id, root_ord, *node_ords) in api_matches:
            source = sentences_by_id.get(_source_id(treebank, str(root_id)))
            if source is not None:
                index, sentence = source
                trees = list(token_trees(sentence.to_tree()))
                tree_order = {tree.token["id"]: position for position, tree in enumerate(trees)}
                candidate = (sentence, root_ord, node_ords)
                current = matches_by_index.get(index)
                candidate_order = (tree_order[int(root_ord)], *(int(value) for value in node_ords if value is not None))
                if current is None:
                    matches_by_index[index] = candidate
                else:
                    _, current_root_ord, current_node_ords = current
                    current_order = (
                        tree_order[int(current_root_ord)],
                        *(int(value) for value in current_node_ords if value is not None),
                    )
                    if candidate_order < current_order:
                        matches_by_index[index] = candidate

        rows = []
        matched_sentences = 0
        for index, (source_sentence, root_ord, node_ords) in sorted(matches_by_index.items()):
            if limit is not None and len(rows) >= limit:
                break

            sentence = deepcopy(source_sentence)
            trees = {
                tree.token["id"]: tree
                for tree in token_trees(sentence.to_tree())
            }
            root_tree = trees[int(root_ord)]
            match: Match = {"root": root_tree.token, "root_tree": root_tree}
            for node, node_ord in zip(variant.nodes, node_ords):
                if node_ord is None:
                    continue
                tree = trees[int(node_ord)]
                match[node] = tree.token
                match[f"{node}_tree"] = tree

            matched_sentences += 1
            metadata = sentence.metadata or {}
            correct_text = metadata.get("text") or sentence_text(sentence)
            random.seed(f"{variant.seed_namespace}:{correct_text}")
            if not variant.transform(sentence, match):
                continue

            incorrect_text = sentence_text(sentence)
            assert correct_text != incorrect_text
            rows.append((metadata.get("dataset", ""), index, correct_text, incorrect_text))

        frame = pd.DataFrame(rows, columns=["dataset", "conllu_index", "correct", "incorrect"])
        frame.attrs["matched_sentences"] = matched_sentences
        frames.append(frame)

    result = pd.concat(frames, ignore_index=True)
    result.attrs["matched_sentences"] = sum(frame.attrs["matched_sentences"] for frame in frames)
    return result


def _treebanks_for_sentences(sentences: list[conllu.TokenList]) -> list[str]:
    datasets = {str((sentence.metadata or {}).get("dataset", "")) for sentence in sentences}
    return [treebank for treebank in TREEBANKS if any(name.startswith(f"pl_{treebank}-") for name in datasets)]


def _source_id(treebank: str, root_id: str) -> tuple[str, str]:
    if treebank == "lfg":
        match = re.match(r"pl-lfg-(dev|test|train)\.(\d+)-", root_id)
    elif treebank == "pdb":
        match = re.match(r"pl-pdb-(dev|test|train)\.s(\d+)-", root_id)
    else:
        raise ValueError(f"Unknown treebank: {treebank}")

    if match is None:
        raise RuntimeError(f"Unexpected PML-TQ node id: {root_id}")
    split, sentence_number = match.groups()
    sentence_prefix = "s" if treebank == "pdb" else ""
    return f"pl_{treebank}-ud-{split}.conllu", f"{split}-{sentence_prefix}{sentence_number}"


def fetch_trees(treebank: str, locations: set[tuple[str, int]]) -> dict[tuple[str, int], conllu.TokenList]:
    if not locations:
        return {}

    location_constraint = " or ".join(
        f"(file() = {_pml_string(filename)} and tree_no() = {tree_number})"
        for filename, tree_number in sorted(locations)
    )
    non_root_query = (
        f"a-node $token := [({location_constraint}), parent a-node $head := []] "
        f">> {TOKEN_COLUMNS.format(head='$head.ord')}"
    )
    root_query = (
        f"a-node $token := [({location_constraint}), conll/deprel = 'root'] "
        f">> {TOKEN_COLUMNS.format(head='0')}"
    )

    rows = query_rows(non_root_query, treebank)
    rows.extend(query_rows(root_query, treebank))
    rows_by_tree: dict[tuple[str, int], list[list[object]]] = {location: [] for location in locations}
    for filename, tree_number, *token in rows:
        rows_by_tree[(str(filename), int(tree_number))].append(token)

    return {
        location: _parse_tree(token_rows)
        for location, token_rows in rows_by_tree.items()
    }


def _pml_string(value: object) -> str:
    return "'" + str(value).replace("\\", "\\\\").replace("'", "\\'") + "'"


def _parse_tree(rows: list[list[object]]) -> conllu.TokenList:
    lines = []
    for token_id, form, lemma, upos, xpos, feats, head, deprel, no_space_after in sorted(
            rows,
            key=lambda row: float(row[0]),
    ):
        misc = "SpaceAfter=No" if no_space_after else "_"
        columns = (token_id, form, lemma, upos, xpos, feats or "_", head, deprel, "_", misc)
        lines.append("\t".join(str(value) for value in columns))
    return conllu.parse("\n".join(lines) + "\n")[0]
