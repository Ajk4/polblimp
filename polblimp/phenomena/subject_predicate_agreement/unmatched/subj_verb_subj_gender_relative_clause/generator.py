from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_gender_root, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_subj_gender_relative_clause(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_subj_gender_relative_clause,
        lambda sentence: change_gender_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_subj_gender_relative_clause",
    )


def match_subj_verb_subj_gender_relative_clause(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}
    root_gender = root_feats.get("Gender")

    if root.token["upos"] != "VERB":
        return False
    if root.token["deprel"] != "root":
        return False
    if root_gender is None:
        return False

    for subj_main in root.children:
        subj_main_feats = subj_main.token["feats"] or {}
        if subj_main.token["upos"] != "NOUN":
            continue
        if subj_main.token["deprel"] != "nsubj":
            continue
        if subj_main_feats.get("Gender") != root_gender:
            continue

        for relcl in subj_main.children:
            relcl_feats = relcl.token["feats"] or {}
            if relcl.token["upos"] != "VERB":
                continue
            if relcl.token["deprel"] != "acl:relcl":
                continue
            if relcl_feats.get("Gender") != root_gender:
                continue

            has_subj_rel = False
            has_objobl = False
            for child in relcl.children:
                child_feats = child.token["feats"] or {}
                if child.token.get("lemma") == "który" and child.token["deprel"] == "nsubj":
                    has_subj_rel = True
                if (
                        child.token["upos"] == "NOUN" and
                        child.token["deprel"] in {"obj", "obl"} and
                        child_feats.get("Gender") is not None and
                        child_feats.get("Gender") != root_gender
                ):
                    has_objobl = True

            if has_subj_rel and has_objobl:
                return True

    return False
