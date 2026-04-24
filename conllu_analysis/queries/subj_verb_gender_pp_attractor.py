from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import change_gender_root, match_descendants, run_filter_transform
from .morph_dictionary import MorphDictionary


def run_subj_verb_gender_pp_attractor(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_gender_pp_attractor,
        lambda sentence: change_gender_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_gender_pp_attractor",
    )


def match_subj_verb_gender_pp_attractor(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}

    if root.token["upos"] != "VERB":
        return False

    root_number = root_feats.get("Number")
    root_gender = root_feats.get("Gender")

    for nsubj in root.children:
        if nsubj.token["upos"] != "NOUN":
            continue
        if nsubj.token["deprel"] != "nsubj":
            continue

        nsubj_feats = nsubj.token["feats"] or {}
        if nsubj_feats.get("Gender") != root_gender:
            continue
        if nsubj_feats.get("Number") != root_number:
            continue

        descendants = match_descendants(
            nsubj,
            lambda token: token["deprel"] in {"nmod", "nmod:poss", "xcomp", "conj"},
        )
        if len(descendants) != 1:
            continue

        for attractor in nsubj.children:
            if attractor.token["upos"] != "NOUN":
                continue
            if attractor.token["deprel"] != "nmod":
                continue

            attractor_feats = attractor.token["feats"] or {}
            if not has_valid_pp_prep(attractor):
                continue

            if root_number == "Sing" and attractor_feats.get("Gender") != root_gender:
                return True

            if root_number == "Plur":
                nsubj_is_masc1 = nsubj_feats.get("SubGender") == "Masc1"
                attractor_is_masc1 = attractor_feats.get("SubGender") == "Masc1"
                if nsubj_is_masc1 != attractor_is_masc1:
                    return True

    return False


def has_valid_pp_prep(attractor: conllu.TokenTree) -> bool:
    for prep in attractor.children:
        if prep.token["upos"] != "ADP":
            continue
        if prep.token["deprel"] != "case":
            continue
        return True
    return False
