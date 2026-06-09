from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    match_subj_verb_person_csubj_1a,
    match_subj_verb_person_csubj_2a,
)


def run_subj_verb_number_csubj(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_number_csubj_1a(sentence)
        return change_number(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_csubj_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_number_csubj__1a",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_number_csubj_2a(sentence)
        return change_number(matches["cop"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_csubj_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_number_csubj__2a",
    )

    variants = [variant_1a, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_number_csubj_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return match_subj_verb_person_csubj_1a(sentence)


def match_subj_verb_number_csubj_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return match_subj_verb_person_csubj_2a(sentence)
