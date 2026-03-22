from __future__ import annotations

import random
from typing import Optional

import conllu
import pandas as pd

from .common import change_morph, run_filter_transform
from .morph_dictionary import MorphDictionary


def run_subj_verb_gender_infinitival(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transformation(token: conllu.Token) -> Optional[conllu.Token]:
        source_xpos = token["xpos"]

        if ':n:' in source_xpos:
            if random.randint(0, 1) == 0:
                target_xpos = source_xpos.replace(":n:", ":m1:")
            else:
                target_xpos = source_xpos.replace(":n:", ":f:")
        else:
            print("Unknown tag", source_xpos)
            return None

        return change_morph(token, morph_dict, target_xpos)

    return run_filter_transform(
        sentences,
        match_subj_verb_gender_infinitival,
        transformation,
        limit=limit,
        progress_desc=f"subj_verb_number_clause",
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
