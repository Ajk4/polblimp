from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, token_trees
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms


def run_subj_verb_gender_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_gender(match["root"], morph_dict)

    def transform_2a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_gender(match["cop"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_1a, "subj_verb_gender_csubj__1a"),
            QueryVariant("2a", ("cop",), transform_2a, "subj_verb_gender_csubj__2a"),
        ),
        limit,
    )


def match_subj_verb_gender_csubj_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        match = match_subj_verb_gender_csubj_1a_for_root(root)
        if match is not None:
            return match

    return None


def match_subj_verb_gender_csubj_1a_for_root(root: conllu.TokenTree) -> dict[str, Token] | None:
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_feats.get("Number") != "Sing":
        return None
    if root_feats.get("Gender") != "Neut":
        return None

    for csubj in root.children:
        csubj_token = csubj.token
        if csubj_token["upos"] != "VERB":
            continue
        if "subj" not in csubj_token["deprel"]:
            continue
        if has_kto_child(csubj):
            continue

        return {
            "root": root_token,
            "csubj": csubj_token,
        }

    return None


def match_subj_verb_gender_csubj_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        match = match_subj_verb_gender_csubj_2a_for_root(root)
        if match is not None:
            return match

    return None


def match_subj_verb_gender_csubj_2a_for_root(root: conllu.TokenTree) -> dict[str, Token] | None:
    root_token = root.token

    if root_token["upos"] == "VERB":
        return None

    csubj_token = None
    for csubj in root.children:
        child_token = csubj.token
        if child_token["upos"] != "VERB":
            continue
        if "subj" not in child_token["deprel"]:
            continue
        if has_kto_child(csubj):
            continue
        csubj_token = child_token
        break

    if csubj_token is None:
        return None

    for cop in root.children:
        cop_token = cop.token
        cop_feats = cop_token["feats"] or {}
        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by"}:
            continue
        if cop_feats.get("Number") != "Sing":
            continue
        if cop_feats.get("Gender") != "Neut":
            continue

        return {
            "root": root_token,
            "csubj": csubj_token,
            "cop": cop_token,
        }

    return None


def has_kto_child(tree: conllu.TokenTree) -> bool:
    return any(child.token["lemma"] == "kto" for child in tree.children)
