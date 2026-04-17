
from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import change_number, run_filter_transform
from .morph_dictionary import MorphDictionary

"""
subj_verb_number_numerals
Change the number of $root.

Query:
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  member iset[number in {'sing', 'plur'}], # check the number

  child a-node $nsubj := [
    tag = 'NOUN',
    deprel = 'nsubj',

    child a-node $num := [
    tag = 'NUM',
    ],

# check for number (if the sentences are annotated correctly)
  ($root.iset/number = 'sing' and $nsubj.iset/case = 'gen' and $num.iset/case = 'acc')
  or
  ($root.iset/number = 'plur' and !($nsubj.iset/case = 'gen' and $num.iset/case = 'acc'))

  ]
]
"""


def run_subj_verb_number_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_numerals,
        lambda sentence: change_number(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_number_numerals",
    )


def match_subj_verb_number_numerals(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return False
    if root.token["deprel"] != "root":
        return False

    root_number = root_feats.get("Number")
    if root_number not in {"Sing", "Plur"}:
        return False

    for child in root.children:
        if child.token["upos"] != "NOUN":
            continue
        if child.token["deprel"] != "nsubj":
            continue

        child_feats = child.token["feats"] or {}
        nsubj_case = child_feats.get("Case")

        for num_child in child.children:
            if num_child.token["upos"] != "NUM":
                continue

            num_child_feats = num_child.token["feats"] or {}
            is_gen_acc = nsubj_case == "Gen" and num_child_feats.get("Case") == "Acc"
            if root_number == "Sing" and is_gen_acc:
                return True
            if root_number == "Plur" and not is_gen_acc:
                return True

    return False
