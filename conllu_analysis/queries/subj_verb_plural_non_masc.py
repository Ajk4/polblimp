from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import match_descendants, run_filter_transform, change_gender
from .morph_dictionary import MorphDictionary


def run_subj_verb_plural_non_masc(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    _ = morph_dict
    return run_filter_transform(
        sentences,
        match_subj_verb_plural_non_masc,
        lambda token: change_gender(token, morph_dict),
        limit=limit,
        progress_desc="subj_verb_plural_non_masc",
    )


def match_subj_verb_plural_non_masc(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return None
    if root_feats.get("Number") != "Plur":
        return None
    if root_feats.get("SubGender") not in {"Masc2", "Masc3"}:
        return None

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
        return root.token

    return None
