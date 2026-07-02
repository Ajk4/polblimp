from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_person, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_person_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_person_csubj_1a(sentence)
        return change_person(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_csubj_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_person_csubj__1a",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_person_csubj_2a(sentence)
        return change_person(matches["cop"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_csubj_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_person_csubj__2a",
    )

    variants = [variant_1a, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


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
        csubj = child_token
        break

    if csubj is None:
        return None

    for cop in root.children:
        cop_token = cop.token
        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by"}:
            continue
        return {
            "root": root_token,
            "csubj": csubj,
            "cop": cop_token,
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


def token_trees(tree: conllu.TokenTree) -> list[conllu.TokenTree]:
    trees = [tree]
    for child in tree.children:
        trees.extend(token_trees(child))
    return trees
