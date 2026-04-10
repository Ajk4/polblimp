from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import change_gender, run_filter_transform
from .morph_dictionary import MorphDictionary


def run_subj_verb_gender_obj_relative_clause_1(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_gender_obj_relative_clause_1,
        lambda sentence: change_gender(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_gender_obj_relative_clause_1",
    )


def match_subj_verb_gender_obj_relative_clause_1(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}
    root_gender = root_feats.get("Gender")
    root_number = root_feats.get("Number")

    if root.token["upos"] != "VERB":
        return False
    if root.token["deprel"] != "root":
        return False

    for subj_main in root.children:
        subj_main_feats = subj_main.token["feats"] or {}
        if subj_main.token["deprel"] != "nsubj":
            continue
        if subj_main.token["upos"] != "NOUN":
            continue
        if subj_main_feats.get("Gender") != root_gender:
            continue
        if subj_main_feats.get("Number") != root_number:
            continue

        for relcl in subj_main.children:
            if relcl.token["deprel"] != "acl:relcl":
                continue
            if relcl.token["upos"] != "VERB":
                continue

            for subj_rel in relcl.children:
                subj_rel_feats = subj_rel.token["feats"] or {}
                if subj_rel.token["deprel"] != "nsubj":
                    continue
                if subj_rel.token["upos"] != "NOUN":
                    continue
                if subj_rel_feats.get("Gender") == subj_main_feats.get("Gender"):
                    continue
                return True

    return False
