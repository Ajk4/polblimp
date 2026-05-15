from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import match_descendants, run_filter_transform, change_person, change_number_root, change_number
from ..morph_dictionary import MorphDictionary
from ..subj_pred_person_simple.generator import match_subj_pred_person_simple, extract_subj_pred_person_simple


def run_subj_pred_number_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_person_simple(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"

        if matches['root']['upos'] == 'ADJ':
            return change_number(matches['root'], morph_dict) and change_number(matches['cop'], morph_dict)
        else:
            return change_number(matches['cop'], morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_pred_person_simple,
        transform,
        limit=limit,
        progress_desc="subj_pred_person_simple",
    )
