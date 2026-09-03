from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_number
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.adjective.adjective_and_copula.subj_adjectival_number_cop.generator import (
    match_subj_adjectival_number_cop,
)


def run_subj_adjectival_number(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["root"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (QueryVariant("1a", ("root",), transform, "subj_adjectival_number"),),
        limit,
    )


def match_subj_adjectival_number(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return match_subj_adjectival_number_cop(sentence)
