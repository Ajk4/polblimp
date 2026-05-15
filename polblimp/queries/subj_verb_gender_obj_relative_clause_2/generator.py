from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import run_filter_transform
from ..morph_dictionary import MorphDictionary
from ..subj_verb_gender_obj_relative_clause_1.generator import match_subj_verb_gender_obj_relative_clause, change_gender_to, \
    extract_subj_verb_gender_obj_relative_clause


def run_subj_verb_gender_obj_relative_clause_2(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_verb_gender_obj_relative_clause(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        token_to_change = matches['relcl']
        target_gender = matches['root']['feats']['Gender']
        return change_gender_to(token_to_change, morph_dict, target_gender)

    return run_filter_transform(
        sentences,
        match_subj_verb_gender_obj_relative_clause,
        transform,
        limit=limit,
        progress_desc="subj_verb_gender_obj_relative_clause_2",
    )
