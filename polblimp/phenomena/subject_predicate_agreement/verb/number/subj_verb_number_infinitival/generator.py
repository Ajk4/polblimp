from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_number_root, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_number_infinitival(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_infinitival,
        lambda sentence: change_number_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_number_infinitival",
    )


def match_subj_verb_number_infinitival(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return False
    if root_feats.get("Number") != "Sing":
        return False

    for child in root.children:
        child_feats = child.token["feats"] or {}
        if (
                child.token["upos"] == "VERB" and
                child.token["deprel"] == "csubj" and
                child_feats.get("VerbForm") == "Inf"
        ):
            return True

    return False
