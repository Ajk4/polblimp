from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import run_filter_transform, change_person_root
from ..morph_dictionary import MorphDictionary


def run_subj_verb_person_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_person_numerals,
        lambda sentence: change_person_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_person_numerals",
    )


def match_subj_verb_person_numerals(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return False
    if root.token["deprel"] != "root":
        return False
    if root_feats.get("Person") != "3":
        return False

    for child in root.children:
        if child.token["upos"] != "NOUN":
            continue
        if child.token["deprel"] != "nsubj":
            continue

        for num_child in child.children:
            if num_child.token["upos"] == "NUM":
                return True

    return False
