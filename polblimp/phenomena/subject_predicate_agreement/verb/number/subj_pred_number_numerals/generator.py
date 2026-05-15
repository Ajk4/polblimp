from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.unmatched.subj_pred_person_numerals.generator import (
    extract_subj_pred_person_numerals as extract_subj_pred_number_numerals,
    match_subj_pred_person_numerals as match_subj_pred_number_numerals,
)


def run_subj_pred_number_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_number_numerals(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"

        nsubj_feats = matches["nsubj"]["feats"] or {}
        nsubj_case = nsubj_feats.get("Case")

        if nsubj_case == "Nom":
            if matches["root"]["upos"] == "ADJ":
                return change_number(matches["cop"], morph_dict) and change_number(matches["root"], morph_dict)
            else:
                return change_number(matches["cop"], morph_dict)
        if nsubj_case == "Gen":
            return change_number(matches["cop"], morph_dict)

        return False

    return run_filter_transform(
        sentences,
        match_subj_pred_number_numerals,
        transform,
        limit=limit,
        progress_desc="subj_pred_number_numerals",
    )
