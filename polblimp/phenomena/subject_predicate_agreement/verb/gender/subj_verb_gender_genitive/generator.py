from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import run_filter_transform, change_gender_root
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_gender_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_gender_genitive,
        lambda sentence: change_gender_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_gender_genitive",
    )


def match_subj_verb_gender_genitive(
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
    if root_feats.get("Gender") != "Neut":
        return False

    for child in root.children:
        child_feats = child.token["feats"] or {}
        if child.token["deprel"] != "nsubj":
            continue
        if child_feats.get("Case") != "Gen":
            continue

        has_num_child = False
        for subject_child in child.children:
            if subject_child.token["upos"] == "NUM":
                has_num_child = True
                break

        if not has_num_child:
            return True

    return False
