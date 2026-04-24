from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import match_descendants, run_filter_transform, change_gender_root
from .morph_dictionary import MorphDictionary


def run_subj_verb_plural_masc(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_plural_masc,
        lambda sentence: change_gender_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_plural_masc",
    )


def match_subj_verb_plural_masc(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return False
    if root_feats.get("Number") != "Plur":
        return False
    if root_feats.get("SubGender") != "Masc1":
        return False

    root_gender = root_feats.get("Gender")
    for child in root.children:
        child_feats = child.token["feats"] or {}
        if child.token["upos"] != "NOUN":
            continue
        if child.token["deprel"] != "nsubj":
            continue

        descendants = match_descendants(
            child,
            lambda token: token["deprel"] in {"nmod", "nmod:poss", "xcomp", "conj"},
        )
        if descendants:
            continue

        if child_feats.get("Gender") != root_gender:
            continue
        if child_feats.get("Number") != root_feats.get("Number"):
            continue
        return True

    return False
