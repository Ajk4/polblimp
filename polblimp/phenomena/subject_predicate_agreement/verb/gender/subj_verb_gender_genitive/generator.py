from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_genitive.generator import (
    has_numeral_or_quantifier_child,
)


def run_subj_verb_gender_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_genitive_1a(sentence)
        return change_gender(matches["root"], morph_dict)

    return run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_genitive_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_genitive__1a",
    )


def match_subj_verb_gender_genitive_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_feats.get("Number") != "Sing":
        return None
    if root_feats.get("Gender") != "Neut":
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Case") != "Gen":
            continue
        if has_numeral_or_quantifier_child(nsubj):
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
        }

    return None
