from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import QUANTIFIER_LEMMAS, change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_number_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_number_genitive_1a(sentence)
        return change_number(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_genitive_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_number_genitive__1a",
    )

    return variant_1a


def match_subj_verb_number_genitive_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_feats.get("Number") != "Sing":
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Case") != "Gen":
            continue
        if has_numeral_or_quantifier_child(nsubj):
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
        }

    return None


def has_numeral_or_quantifier_child(nsubj: conllu.TokenTree) -> bool:
    for child in nsubj.children:
        child_token = child.token
        if child_token["upos"] == "NUM":
            return True
        if child_token["deprel"].startswith("det") and child_token["lemma"] in QUANTIFIER_LEMMAS:
            return True

    return False
