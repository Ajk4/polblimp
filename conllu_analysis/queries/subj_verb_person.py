from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import run_filter_transform, change_gender
from .morph_dictionary import MorphDictionary

"""
a-node $root := [
  tag = 'VERB',
  deprel = 'root',
  
  child a-node $nsubj := [
    tag = 'PRON',
    deprel = 'nsubj',
  ],
  
  (
    # W czasach teraźniejszym i przyszłym trzeba zmienić osobę $roota
    ($root.iset/tense in{'present', 'fut'} and $root.iset/person in{'1', '2', '3'} and $nsubj.iset/person = $root.iset/person)
    or
    # W czasie przeszłym przy osobach 1 i 2, trzeba zmienić osobę węzła o własnosci deprel = 'aux:clitic' lub usunąć ten węzeł
    ($root.iset/tense = 'past' and child [deprel = 'aux:clitic'] and $nsubj.iset/person in{'1', '2'})
    or
    # W czasie przeszłym przy osobie 3, trzeba dodać do $roota węzeł o własności deprel = 'aux clitic'
    ($root.iset/tense = 'past' and $nsubj.iset/person = '3')
  )
]
"""


def run_subj_verb_person(sentences: list[conllu.TokenList], morph_dict: MorphDictionary,
                         limit: Optional[int], ) -> pd.DataFrame:
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
