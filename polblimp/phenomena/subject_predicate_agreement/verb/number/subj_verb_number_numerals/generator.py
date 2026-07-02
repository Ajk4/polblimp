from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_numerals.generator import (
    match_subj_verb_person_numerals_1a,
    match_subj_verb_person_numerals_1b,
    match_subj_verb_person_numerals_1c,
    match_subj_verb_person_numerals_2a,
    match_subj_verb_person_numerals_2b,
)


def run_subj_verb_number_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_number_numerals_1a(sentence)
        return change_number(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_numerals_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_number_numerals__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_number_numerals_1b(sentence)
        return change_number(matches["root"], morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_numerals_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_number_numerals__1b",
    )

    def transform_1c(sentence) -> bool:
        matches = match_subj_verb_number_numerals_1c(sentence)
        root_feats = matches["root"]["feats"] or {}
        if not change_number(matches["aux"], morph_dict):
            return False
        if root_feats.get("VerbForm") == "Fin":
            return change_number(matches["root"], morph_dict)
        return True

    variant_1c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_numerals_1c(s) is not None,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_number_numerals__1c",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_number_numerals_2a(sentence)
        return change_number(matches["cop"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_numerals_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_number_numerals__2a",
    )

    def transform_2b(sentence) -> bool:
        matches = match_subj_verb_number_numerals_2b(sentence)
        return change_number(matches["cop"], morph_dict)

    variant_2b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_numerals_2b(s) is not None,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_number_numerals__2b",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a, variant_2b]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_number_numerals_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    matches = match_subj_verb_person_numerals_1a(sentence)
    return matches[0] if matches else None


def match_subj_verb_number_numerals_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    matches = match_subj_verb_person_numerals_1b(sentence)
    return matches[0] if matches else None


def match_subj_verb_number_numerals_1c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    matches = match_subj_verb_person_numerals_1c(sentence)
    return matches[0] if matches else None


def match_subj_verb_number_numerals_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    matches = match_subj_verb_person_numerals_2a(sentence)
    return matches[0] if matches else None


def match_subj_verb_number_numerals_2b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    matches = match_subj_verb_person_numerals_2b(sentence)
    return matches[0] if matches else None
