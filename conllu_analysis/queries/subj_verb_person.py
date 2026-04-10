from __future__ import annotations

import random
from typing import Optional

import conllu
import pandas as pd

from .common import run_filter_transform, change_person
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
    variant_1 = run_filter_transform(
        sentences,
        match_subj_verb_person__1,
        lambda token: change_person(token, morph_dict),
        limit=limit,
        progress_desc="subj_verb_person__1",
    )

    variant_2 = run_filter_transform(
        sentences,
        match_subj_verb_person__2,
        remove_aux_clitic,
        limit=limit,
        progress_desc="subj_verb_person__2",
    )

    variant_3 = run_filter_transform(
        sentences,
        match_subj_verb_person__3,
        append_aux_clitic,
        limit=limit,
        progress_desc="subj_verb_person__3",
    )

    df = pd.concat([variant_1, variant_2, variant_3])
    df = variant_3
    df.attrs["matched_sentences"] = len(variant_1) + len(variant_2)
    return df


def append_aux_clitic(sentence: conllu.TokenList) -> bool:
    root = sentence.to_tree().token
    root_form = root['form']
    if random.randint(0, 1) == 0:
        root['form'] = root_form + "em"
    else:
        root['form'] = root_form + "eś"
    return True

def remove_aux_clitic(sentence: conllu.TokenList) -> bool:
    root = sentence.to_tree().token
    root_id = root["id"]
    clitic_indexes = [
        index
        for index, token in enumerate(sentence)
        if token.get("head") == root_id and token.get("deprel") == "aux:clitic"
    ]
    if not clitic_indexes:
        return False

    clitic_misc = sentence[clitic_indexes[-1]].get("misc") or {}
    root_misc = {
        key: value
        for key, value in (root.get("misc") or {}).items()
        if key != "SpaceAfter"
    }
    root_misc.update({
        key: value
        for key, value in clitic_misc.items()
        if key == "SpaceAfter"
    })
    root["misc"] = root_misc or None

    for index in reversed(clitic_indexes):
        del sentence[index]

    return True

def match_subj_verb_person__1(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    if not (root.token["deprel"] == 'root' and root.token["upos"] == "VERB"):
        return False

    root_feats = root.token['feats']

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token['feats']

        if not (nsubj_token["upos"] == "PRON" and nsubj_token["deprel"] == "nsubj"):
            continue

        if (root_feats.get('Tense', '') in {"Pres", "Fut"} and root_feats.get('Person', '') in {'1', '2', '3'} and
                nsubj_feats.get('Person', '') == root_feats.get('Person', '')):
            return True

    return False


def match_subj_verb_person__2(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    if not (root.token["deprel"] == 'root' and root.token["upos"] == "VERB"):
        return False

    root_feats = root.token['feats']

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token['feats']

        if not (nsubj_token["upos"] == "PRON" and nsubj_token["deprel"] == "nsubj"):
            continue

        if root_feats.get('Tense', '') in {"Past", "Fut"} and nsubj_feats.get('Person', '') in {'1', '2'}:
            for clitic in root.children:
                if clitic.token["deprel"] == "aux:clitic":
                    return True

    return False


def match_subj_verb_person__3(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    if not (root.token["deprel"] == 'root' and root.token["upos"] == "VERB"):
        return False

    root_feats = root.token['feats']

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token['feats']

        if not (nsubj_token["upos"] == "PRON" and nsubj_token["deprel"] == "nsubj"):
            continue

        if root_feats.get('Tense', '') in {"Past"} and nsubj_feats.get('Person', '') in {'3'}:
            return True

    return False
