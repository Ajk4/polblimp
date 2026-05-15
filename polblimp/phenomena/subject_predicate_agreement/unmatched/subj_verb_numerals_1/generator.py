from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_number_root, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_numerals_1(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_numerals_1,
        lambda sentence: change_number_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_numerals_1",
    )


def match_subj_verb_numerals_1(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return False
    if root_feats.get("Number") != "Plur":
        return False

    for child in root.children:
        if child.token["upos"] != "NOUN":
            continue
        if child.token["deprel"] != "nsubj":
            continue

        child_feats = child.token["feats"] or {}
        nsubj_case = child_feats.get("Case")
        for num_child in child.children:
            if num_child.token["upos"] != "NUM":
                continue

            num_child_feats = num_child.token["feats"] or {}
            if not (nsubj_case == "Gen" and num_child_feats.get("Case") == "Acc"):
                return True

    return False
