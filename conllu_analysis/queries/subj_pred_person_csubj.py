
"""
subj_pred_person_csubj
The default for csubj is 3 singular neuter.
Change the person of $cop.

Examples:
Chociaż faktem jest, że Hubal okropnie przeżył te zdarzenia.
*Chociaż faktem jesteś, że Hubal okropnie przeżył te zdarzenia.

Query:
a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $clausal := [
    tag = 'VERB',
    deprel = 'csubj',
  ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]
"""

from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import change_person, run_filter_transform
from .morph_dictionary import MorphDictionary
from .subj_pred_number_csubj import (
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
