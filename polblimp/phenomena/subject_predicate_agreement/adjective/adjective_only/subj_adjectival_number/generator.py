from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.adjective.adjective_and_copula.subj_adjectival_number_cop.generator import (
    match_subj_adjectival_number_cop,
)


def run_subj_adjectival_number(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = match_subj_adjectival_number(sentence)
        match = matches[0]
        return change_number(match["root"], morph_dict)

    return run_filter_transform(
        sentences,
        lambda s: len(match_subj_adjectival_number(s)) != 0,
        transform,
        limit=limit,
        progress_desc="subj_adjectival_number",
    )


def match_subj_adjectival_number(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return match_subj_adjectival_number_cop(sentence)
