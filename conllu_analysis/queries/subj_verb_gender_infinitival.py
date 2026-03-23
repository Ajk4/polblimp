from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import change_gender, run_filter_transform
from .morph_dictionary import MorphDictionary


def run_subj_verb_gender_infinitival(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_gender_infinitival,
        lambda token: change_gender(token, morph_dict),
        limit=limit,
        progress_desc="subj_verb_gender_infinitival",
    )


def match_subj_verb_gender_infinitival(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    root_feats = root.token['feats']
    if (root.token["upos"] == "VERB" and root.token["deprel"] == "root" and
            root_feats.get("Number", "") == 'Sing' and root_feats.get("Gender", "") == "Neut"):
        for infinitive in root.children:
            infinitive_feats = infinitive.token['feats']
            if infinitive.token["upos"] == "VERB" and infinitive.token["deprel"] == "csubj" and infinitive_feats.get(
                    'VerbForm', "") == "Inf":
                return root.token
    return None
