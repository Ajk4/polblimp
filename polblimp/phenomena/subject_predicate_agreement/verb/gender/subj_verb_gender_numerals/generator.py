from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, match_descendants, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_numerals.generator import QUANTIFIER_LEMMAS


def run_subj_verb_gender_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_numerals_1a(sentence)
        return change_numeral_predicate_gender(matches["root"], matches["nsubj"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_numerals_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_numerals__1a",
    )

    # Copular auxiliary verb
    def transform_2a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_numerals_2a(sentence)
        return change_numeral_predicate_gender(matches["cop"], matches["nsubj"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_numerals_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_gender_numerals__2a",
    )

    variants = [variant_1a, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_gender_numerals_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_feats.get("Gender") not in {"Masc", "Fem", "Neut"}:
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["upos"] != "NOUN":
            continue
        if nsubj_token["deprel"] not in {"nsubj", "obj"}:
            continue
        numeral_agreement_pattern = (
            (root_feats.get("Number") == "Sing" and nsubj_feats.get("Case") == "Gen")
            or (root_feats.get("Number") == "Plur" and nsubj_feats.get("Case") == "Nom")
        )
        if not numeral_agreement_pattern:
            continue

        num = extract_numeral(nsubj)
        if num is None:
            continue
        if nsubj_token["deprel"] == "obj" and "NumForm" not in (num["feats"] or {}):
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
            "num": num,
        }

    return None


def match_subj_verb_gender_numerals_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass", "obl"}:
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
            if cop_feats.get("Tense") != "Past":
                continue
            nsubj_case = nsubj_feats.get("Case")
            copular_numeral_agreement = (
                (cop_feats.get("Gender") == "Neut" and nsubj_case == "Gen")
                or (cop_feats.get("Gender") == nsubj_feats.get("Gender") and nsubj_case == "Nom")
            )
            if not copular_numeral_agreement:
                continue

            return {
                "root": root_token,
                "nsubj": nsubj_token,
                "num": num,
                "cop": cop_token,
            }

    return None


def extract_numeral(tree: conllu.TokenTree) -> Token | None:
    descendants = match_descendants(
        tree,
        lambda token: (
            token["head"] == tree.token["id"]
            and (
                token["upos"] == "NUM"
                or (token["deprel"] == "det" and token["lemma"] in QUANTIFIER_LEMMAS)
            )
        ) or (
            token["upos"] == "NUM"
            and "NumForm" in (token["feats"] or {})
        ),
    )
    return descendants[0] if descendants else None


def extract_numeral_child(tree: conllu.TokenTree) -> Token | None:
    for child in tree.children:
        child_token = child.token
        if child_token["upos"] == "NUM":
            return child_token
        if child_token["deprel"] == "det" and child_token["lemma"] in QUANTIFIER_LEMMAS:
            return child_token

    return None


def change_numeral_predicate_gender(
        predicate: Token,
        nsubj: Token,
        morph_dict: MorphDictionary,
) -> bool:
    target_gender = get_target_gender_for_numeral_predicate(predicate, nsubj)

    if target_gender is None or predicate_xpos_has_target_gender(predicate["xpos"], target_gender):
        return False

    return change_gender(predicate, morph_dict, target_gender=target_gender)


def get_target_gender_for_numeral_predicate(predicate: Token, nsubj: Token) -> str | None:
    predicate_feats = predicate["feats"] or {}
    nsubj_feats = nsubj["feats"] or {}

    if nsubj_feats.get("Case") == "Gen":
        if predicate_feats.get("Gender") == "Neut":
            return nsubj_feats.get("Gender")
        return "Neut"

    if nsubj_feats.get("Case") == "Nom":
        return "Fem" if is_plural_masculine_personal_xpos(predicate["xpos"]) else "Masc"

    return None


def is_plural_masculine_personal_xpos(xpos: str) -> bool:
    return ":pl:m1" in xpos


def predicate_xpos_has_target_gender(xpos: str, target_gender: str) -> bool:
    if target_gender == "Masc":
        if ":sg:" in xpos:
            return ":sg:m" in xpos or ":sg:m1.m2.m3:" in xpos
        if ":pl:" in xpos:
            return is_plural_masculine_personal_xpos(xpos)
    if target_gender == "Fem":
        if ":sg:" in xpos:
            return ":f:" in xpos
        if ":pl:" in xpos:
            return not is_plural_masculine_personal_xpos(xpos)
    if target_gender == "Neut":
        return ":sg:n" in xpos or ":sg:n1.n2:" in xpos
    return False
