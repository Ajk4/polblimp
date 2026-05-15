from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_number_root, match_descendants, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_number_relational_noun(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_relational_noun,
        lambda sentence: change_number_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_number_relational_noun",
    )


def match_subj_verb_number_relational_noun(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    if root.token["upos"] != "VERB":
        return False

    root_feats = root.token["feats"] or {}
    root_number = root_feats.get("Number")
    if root_number is None:
        return False

    for child in root.children:
        child_feats = child.token["feats"] or {}
        if child.token["upos"] != "NOUN":
            continue
        if child.token["deprel"] != "nsubj":
            continue
        if child_feats.get("Number") != root_number:
            continue

        descendants = match_descendants(
            child,
            lambda token: token["deprel"] in {"nmod", "nmod:poss", "xcomp", "conj"},
        )
        if len(descendants) != 1:
            continue

        for attractor in child.children:
            attractor_feats = attractor.token["feats"] or {}
            attractor_number = attractor_feats.get("Number")
            if attractor.token["upos"] != "NOUN":
                continue
            if attractor.token["deprel"] != "nmod:poss":
                continue
            if attractor_number is None:
                continue
            if attractor_number == root_number:
                continue
            return True

    return False
