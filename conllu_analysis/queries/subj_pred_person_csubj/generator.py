from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import change_person, run_filter_transform
from ..morph_dictionary import MorphDictionary
from ..subj_pred_number_csubj.generator import (
    extract_subj_pred_number_csubj as extract_subj_pred_person_csubj,
    match_subj_pred_number_csubj as match_subj_pred_person_csubj,
)


def run_subj_pred_person_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_person_csubj(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"
        return change_person(matches["cop"], morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_pred_person_csubj,
        transform,
        limit=limit,
        progress_desc="subj_pred_person_csubj",
    )
