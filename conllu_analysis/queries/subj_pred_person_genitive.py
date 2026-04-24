
from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import run_filter_transform, change_person
from .morph_dictionary import MorphDictionary

"""
a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    member iset [ case = 'gen' ],
    0x child [tag = 'NUM'] # if we dont want numerals
  ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]

"""


def run_subj_pred_person_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_person_genitive(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        return change_person(matches['cop'], morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_pred_person_genitive,
        transform,
        limit=limit,
        progress_desc="subj_pred_person_genitive",
    )


def match_subj_pred_person_genitive(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_pred_person_genitive(sentence) is not None


def extract_subj_pred_person_genitive(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    if root.token["upos"] == "VERB":
        return None
    if root.token["deprel"] != "root":
        return None

    nsubj = None
    for child in root.children:
        child_feats = child.token["feats"] or {}
        if child.token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        if child_feats.get("Case") != "Gen":
            continue

        has_num_child = False
        for subj_child in child.children:
            if subj_child.token["upos"] == "NUM":
                has_num_child = True
                break
        if has_num_child:
            continue

        nsubj = child
        break

    if nsubj is None:
        return None

    cop = None
    for child in root.children:
        if child.token["upos"] != "AUX":
            continue
        if child.token.get("lemma") in {"to", "by"}:
            continue
        cop = child
        break

    if cop is None:
        return None

    return {
        "root": root.token,
        "nsubj": nsubj.token,
        "cop": cop.token,
    }
