from __future__ import annotations
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import run_filter_transform, change_person, match_children, append_aux_clitic
from phenomena.morph_dictionary import MorphDictionary


QUANTIFIER_LEMMAS = {
    "kilka",
    "kilkaset",
    "kilkanaście",
    "kilkadziesiąt",
    "sporo",
    "mnóstwo",
    "dużo",
    "wiele",
    "więcej",
    "najwięcej",
    "większość",
    "mało",
    "mniej",
    "najmniej",
    "trochę",
    "parę",
    "niewiele",
    "ile",
    "tyle",
}


def run_subj_verb_person_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_person_numerals_1a(sentence)
        return change_person(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_numerals_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_person_numerals__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_person_numerals_1b(sentence)
        return append_aux_clitic(matches["root"], morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_numerals_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_person_numerals__1b",
    )

    def transform_1c(sentence) -> bool:
        matches = match_subj_verb_person_numerals_1c(sentence)
        return change_person(matches["aux"], morph_dict)

    variant_1c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_numerals_1c(s) is not None,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_person_numerals__1c",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_person_numerals_2a(sentence)
        return change_person(matches["cop"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_numerals_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_person_numerals__2a",
    )

    def transform_2b(sentence) -> bool:
        matches = match_subj_verb_person_numerals_2b(sentence)
        return append_aux_clitic(matches["cop"], morph_dict)

    variant_2b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_numerals_2b(s) is not None,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_person_numerals__2b",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a, variant_2b]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_person_numerals_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_feats.get("Tense") not in {"Pres", "Fut"}:
        return None
    if root_feats.get("Person") != "3":
        return None

    return extract_main_verb_numeral_match(root, check_root_number=True)


def match_subj_verb_person_numerals_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if not (root_feats.get("Tense") == "Past" or root_token["lemma"] == "powinien"):
        return None
    if len(match_children(root, lambda token: token["deprel"] == "aux")) != 0:
        return None

    return extract_main_verb_numeral_match(root, check_root_number=True)


def match_subj_verb_person_numerals_1c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_token["lemma"] == "to":
        return None

    base_match = extract_main_verb_numeral_match(root, check_root_number=False)
    if base_match is None:
        return None

    nsubj_feats = base_match["nsubj"]["feats"] or {}
    for aux in root.children:
        aux_token = aux.token
        aux_feats = aux_token["feats"] or {}
        if aux_token["deprel"] != "aux":
            continue
        if not agrees_with_numeral_subject(aux_feats.get("Number"), nsubj_feats.get("Case")):
            continue
        return {
            **base_match,
            "aux": aux_token,
        }

    return None


def match_subj_verb_person_numerals_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_copular_numeral_match(sentence)
    if match is None:
        return None

    cop_feats = match["cop"]["feats"] or {}
    if cop_feats.get("Tense") in {"Pres", "Fut"}:
        return match

    return None


def match_subj_verb_person_numerals_2b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_copular_numeral_match(sentence)
    if match is None:
        return None

    cop_feats = match["cop"]["feats"] or {}
    if cop_feats.get("Tense") == "Past":
        return match

    return None


def extract_main_verb_numeral_match(
        root: conllu.TokenTree,
        check_root_number: bool,
) -> dict[str, Token] | None:
    root_token = root.token
    root_feats = root_token["feats"] or {}
    root_number = root_feats.get("Number")

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["upos"] != "NOUN":
            continue
        if nsubj_token["deprel"] != "nsubj":
            continue
        if check_root_number and not agrees_with_numeral_subject(root_number, nsubj_feats.get("Case")):
            continue

        num = extract_numeral_child(nsubj)
        if num is None:
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
            "num": num,
        }

    return None


def extract_copular_numeral_match(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue

        num = extract_numeral_child(nsubj)
        if num is None:
            continue

        for cop in root.children:
            cop_token = cop.token
            cop_feats = cop_token["feats"] or {}
            if cop_token["upos"] != "AUX":
                continue
            if cop_token["lemma"] in {"to", "by"}:
                continue
            if not agrees_with_numeral_subject(cop_feats.get("Number"), nsubj_feats.get("Case")):
                continue
            return {
                "root": root_token,
                "nsubj": nsubj_token,
                "num": num,
                "cop": cop_token,
            }

    return None


def extract_numeral_child(nsubj: conllu.TokenTree) -> Token | None:
    for child in nsubj.children:
        child_token = child.token
        if child_token["upos"] == "NUM":
            return child_token
        if child_token["deprel"] == "det" and child_token["lemma"] in QUANTIFIER_LEMMAS:
            return child_token

    return None


def agrees_with_numeral_subject(number: str | None, nsubj_case: str | None) -> bool:
    return (
        (number == "Sing" and nsubj_case == "Gen")
        or (number == "Plur" and nsubj_case == "Nom")
    )
