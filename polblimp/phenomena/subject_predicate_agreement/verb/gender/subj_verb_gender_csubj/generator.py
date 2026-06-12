from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_gender_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_csubj_1a(sentence)
        return change_gender(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_csubj_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_csubj__1a",
    )

    def transform_2a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_csubj_2a(sentence)
        return change_gender(matches["cop"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_csubj_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_gender_csubj__2a",
    )

    variants = [variant_1a, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_gender_csubj_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
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

        return {
            "root": root_token,
            "csubj": csubj_token,
        }

    return None


def match_subj_verb_gender_csubj_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["upos"] == "VERB":
        return None
    if root_token["deprel"] != "root":
        return None

    csubj_token = None
    for csubj in root.children:
        child_token = csubj.token
        if child_token["upos"] != "VERB":
            continue
        if "subj" not in child_token["deprel"]:
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
