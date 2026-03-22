from __future__ import annotations

from functools import partial
from typing import Optional

import conllu
import pandas as pd

from .common import change_number, run_filter_transform
from .morph_dictionary import MorphDictionary


def run_subj_verb_numerals_2(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_numerals_2,
        partial(change_number, morph_dict=morph_dict),
        limit=limit,
        progress_desc="subj_verb_numerals_2",
    )


def match_subj_verb_numerals_2(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return None
    if root_feats.get("Number") != "Sing":
        return None

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
            if nsubj_case == "Gen" and num_child_feats.get("Case") == "Acc":
                return root.token

    return None
