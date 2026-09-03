from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_number
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    match_subj_verb_person_csubj_1a,
    match_subj_verb_person_csubj_2a,
)


def run_subj_verb_number_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["root"], morph_dict)

    def transform_2a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["cop"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_1a, "subj_verb_number_csubj__1a"),
            QueryVariant("2a", ("cop",), transform_2a, "subj_verb_number_csubj__2a"),
        ),
        limit,
    )


def match_subj_verb_number_csubj_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return match_subj_verb_person_csubj_1a(sentence)


def match_subj_verb_number_csubj_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return match_subj_verb_person_csubj_2a(sentence)
