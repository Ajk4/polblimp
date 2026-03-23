from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import run_filter_transform, change_gender
from .morph_dictionary import MorphDictionary


def run_subj_verb_person(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    _ = morph_dict
    return run_filter_transform(
        sentences,
        match_subj_verb_person,
        lambda token: change_gender(token, morph_dict),
        limit=limit,
        progress_desc="subj_verb_person",
    )


def match_subj_verb_person(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    if root.token["upos"] != "VERB":
        return None

    for child in root.children:
        child_token = child.token
        if child_token["upos"] == "PRON" and child_token["deprel"] == "nsubj":
            return root.token

    return None
