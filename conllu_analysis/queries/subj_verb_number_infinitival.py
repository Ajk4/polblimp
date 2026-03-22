from __future__ import annotations

from functools import partial
from typing import Optional

import conllu
import pandas as pd

from .common import change_number, run_filter_transform
from .morph_dictionary import MorphDictionary


def run_subj_verb_number_infinitival(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_infinitival,
        partial(change_number, morph_dict=morph_dict),
        limit=limit,
        progress_desc="subj_verb_number_infinitival",
    )


def match_subj_verb_number_infinitival(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return None
    if root_feats.get("Number") != "Sing":
        return None

    for child in root.children:
        child_feats = child.token["feats"] or {}
        if (
                child.token["upos"] == "VERB" and
                child.token["deprel"] == "csubj" and
                child_feats.get("VerbForm") == "Inf"
        ):
            return root.token

    return None
