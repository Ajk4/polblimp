from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import token_trees
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.verb.person.common import (
    change_person,
)


def run_subj_verb_person_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_person(match["root_tree"], morph_dict)

    def transform_2a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_person(match["cop_tree"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_1a, "subj_verb_person_csubj__1a"),
            QueryVariant("2a", ("cop",), transform_2a, "subj_verb_person_csubj__2a"),
        ),
        limit,
    )


def match_subj_verb_person_csubj_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        match = match_subj_verb_person_csubj_1a_for_root(root)
        if match is not None:
            return match

    return None


def match_subj_verb_person_csubj_1a_for_root(root: conllu.TokenTree) -> dict[str, Token] | None:
    root_token = root.token

    if root_token["upos"] != "VERB":
        return None
    if not is_singular_verb_for_csubj(root_token):
        return None

    for csubj in root.children:
        csubj_token = csubj.token
        if csubj_token["upos"] != "VERB":
            continue
        if "subj" not in csubj_token["deprel"]:
            continue
        if has_kto_child(csubj) and not has_correlative_ten_child(root):
            continue
        return {
            "root": root_token,
            "root_tree": root,
            "csubj": csubj_token,
        }

    return None


def match_subj_verb_person_csubj_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        match = match_subj_verb_person_csubj_2a_for_root(root)
        if match is not None:
            return match

    return None


def match_subj_verb_person_csubj_2a_for_root(root: conllu.TokenTree) -> dict[str, Token] | None:
    root_token = root.token

    if root_token["upos"] == "VERB":
        return None

    csubj = None
    for child in root.children:
        child_token = child.token
        if child_token["upos"] != "VERB":
            continue
        if "subj" not in child_token["deprel"]:
            continue
        if has_kto_child(child):
            continue
        csubj = child_token
        break

    if csubj is None:
        return None

    for cop in root.children:
        cop_token = cop.token
        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by", "niech"}:
            continue
        return {
            "root": root_token,
            "csubj": csubj,
            "cop": cop_token,
            "cop_tree": cop,
        }

    return None


def has_kto_child(tree: conllu.TokenTree) -> bool:
    return any(child.token["lemma"] == "kto" for child in tree.children)


def has_correlative_ten_child(tree: conllu.TokenTree) -> bool:
    return any(child.token["lemma"] == "ten" for child in tree.children)


def is_singular_verb_for_csubj(token: Token) -> bool:
    feats = token["feats"] or {}
    if feats.get("Number") == "Sing":
        return True
    return token["lemma"] == "to" and token["xpos"] == "pred"
