from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import change_person, run_filter_transform
from ..morph_dictionary import MorphDictionary


def run_subj_pred_person_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_person_numerals(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        return change_person(matches["cop"], morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_pred_person_numerals,
        transform,
        limit=limit,
        progress_desc="subj_pred_person_numerals",
    )


def match_subj_pred_person_numerals(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_pred_person_numerals(sentence) is not None


def extract_subj_pred_person_numerals(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    if root.token["upos"] == "VERB":
        return None
    if root.token["deprel"] != "root":
        return None

    nsubj = None
    num = None
    for child in root.children:
        if child.token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue

        for subj_child in child.children:
            if subj_child.token["upos"] == "NUM":
                num = subj_child
                break

        if num is None:
            continue

        nsubj = child
        break

    if nsubj is None:
        return None
    assert num is not None

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
        "nsubj": nsubj.token,
        "num": num.token,
        "cop": cop.token,
    }
