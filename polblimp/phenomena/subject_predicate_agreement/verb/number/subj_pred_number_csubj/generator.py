
from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_pred_number_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_number_csubj(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        return change_number(matches["cop"], morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_pred_number_csubj,
        transform,
        limit=limit,
        progress_desc="subj_pred_number_csubj",
    )


def match_subj_pred_number_csubj(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_pred_number_csubj(sentence) is not None


def extract_subj_pred_number_csubj(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    if root.token["upos"] == "VERB":
        return None
    if root.token["deprel"] != "root":
        return None

    clausal = None
    for child in root.children:
        if child.token["upos"] != "VERB":
            continue
        if child.token["deprel"] != "csubj":
            continue
        clausal = child
        break

    if clausal is None:
        return None

    cop = None
    for child in root.children:
        if child.token["upos"] != "AUX":
            continue
        if child.token.get("lemma") in {"to", "by"}:
            continue
        cop = child
        break

    if cop is None:
        return None

    return {
        "root": root.token,
        "clausal": clausal.token,
        "cop": cop.token,
    }
