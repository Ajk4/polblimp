
from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_obj_relative_clause_1.generator import change_gender_to


def run_subj_verb_gender_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_verb_gender_numerals(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        token_to_change = matches["root"]
        root_gender = matches["root"]["feats"]["Gender"]
        if root_gender == "Neut":
            target_gender = matches["nsubj"]["feats"]["Gender"]
        else:
            target_gender = "Neut"

        if root_gender == target_gender:
            return False

        return change_gender_to(token_to_change, morph_dict, target_gender)

    return run_filter_transform(
        sentences,
        match_subj_verb_gender_numerals,
        # lambda sentence: True,
        transform,
        limit=limit,
        progress_desc="subj_verb_gender_numerals",
    )


def match_subj_verb_gender_numerals(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_verb_gender_numerals(sentence) is not None


def extract_subj_verb_gender_numerals(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}
    root_gender = root_feats.get("Gender")

    #  [pl] Dopiero wtedy oba ugrupowania będą mogły mówić o pełnym wyborczym sukcesie.

    if root.token["upos"] != "VERB":
        return None
    if root.token["deprel"] != "root":
        return None
    if root_gender not in {"Masc", "Fem", "Neut"}:
        return None

    for nsubj in root.children:
        if nsubj.token["upos"] != "NOUN":
            continue
        if nsubj.token["deprel"] != "nsubj":
            continue

        nsubj_feats = nsubj.token["feats"] or {}
        nsubj_gender = nsubj_feats.get("Gender")

        for num in nsubj.children:
            if num.token["upos"] != "NUM":
                continue

            num_feats = num.token["feats"] or {}
            is_gen_acc = nsubj_feats.get("Case") == "Gen" and num_feats.get("Case") == "Acc"
            dict = {
                "root": root.token,
                "nsubj": nsubj.token,
                "num": num.token,
            }
            if root_gender == "Neut" and is_gen_acc:
                return dict
            if root_gender == nsubj_gender and not is_gen_acc:
                return dict

    return None
