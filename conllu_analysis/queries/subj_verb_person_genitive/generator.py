from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import change_person_root, run_filter_transform
from ..morph_dictionary import MorphDictionary


def run_subj_verb_person_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    print("TODO Implement pair generation")
    return run_filter_transform(
        sentences,
        match_subj_verb_person_genitive,
        lambda sentence: True, # TODO
        limit=limit,
        progress_desc="subj_verb_person_genitive",
    )


def match_subj_verb_person_genitive(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["deprel"] != "root":
        return False
    if root.token["upos"] != "VERB":
        return False
    if root_feats.get("Number") != "Sing":
        return False

    for child in root.children:
        child_feats = child.token["feats"] or {}
        if child.token["deprel"] != "nsubj":
            continue
        if child_feats.get("Case") != "Gen":
            continue
        return True

    return False
