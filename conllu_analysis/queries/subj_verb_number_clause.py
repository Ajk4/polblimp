
from functools import partial
from typing import Optional

import conllu
import pandas as pd

from .common import run_filter_transform, change_number
from .morph_dictionary import MorphDictionary


def run_subj_verb_number_clause(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_clause,
        partial(change_number, morph_dict=morph_dict),
        limit=limit,
        progress_desc=f"run_subj_verb_number_clause",
    )

# TODO use other
def match_subj_verb_number_clause(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    token_tree = sentence.to_tree()
    token = token_tree.token
    if token["upos"] == "VERB" and token["deprel"] == "root" and "sg" in token["xpos"]:
        for child in token_tree.children:
            child_xpos = child.token["xpos"].split(":")
            if child.token["upos"] == "VERB" and child.token["deprel"] == "csubj" and "inf" not in child_xpos:
                return token
    return None


def match_subj_verb_number_clause2(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    if root.token["upos"] != "VERB":
        return None

    root_feats = root.token['feats']
    if root_feats.get("Number", "") != 'Sing':
        return None

    for child in root.children:
        child_feats = child.token['feats']
        if child.token["upos"] == "VERB" and child.token["deprel"] == "csubj" and child_feats.get("VerbForm",
                                                                                                  "") != "Inf":
            return root.token

    return None
