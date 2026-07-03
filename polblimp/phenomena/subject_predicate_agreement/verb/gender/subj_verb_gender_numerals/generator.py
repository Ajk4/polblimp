from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    QUANTIFIER_LEMMAS,
    agrees_with_numeral_subject,
    change_gender,
    extract_numeral_children,
    match_descendants,
    run_filter_transform,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_gender_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_numerals_1a(sentence)
        return change_numeral_predicate_gender(matches[0]["root"], matches[0]["nsubj"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_gender_numerals_1a(s)),
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_numerals__1a",
    )

    # Copular auxiliary verb
    def transform_2a(sentence: conllu.TokenList) -> bool:
        matches = match_subj_verb_gender_numerals_2a(sentence)
        return change_numeral_predicate_gender(matches[0]["cop"], matches[0]["nsubj"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_gender_numerals_2a(s)),
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_gender_numerals__2a",
    )

    variants = [variant_1a, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_gender_numerals_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_main_verb_gender_numeral_matches(root))

    return matches


def extract_main_verb_gender_numeral_matches(root: conllu.TokenTree) -> list[dict[str, Token]]:
    root_token = root.token
    root_feats = root_token["feats"] or {}
    matches = []

    if root_token["upos"] != "VERB":
        return matches
    if root_feats.get("Gender") not in {"Masc", "Fem", "Neut"}:
        return matches

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["upos"] != "NOUN":
            continue
        if nsubj_token["deprel"] not in {"nsubj", "obj"}:
            continue
        if not agrees_with_numeral_subject(root_feats.get("Number"), nsubj_feats.get("Case")):
            continue

        num = extract_gender_numeral(nsubj)
        if num is None:
            continue
        if not is_main_verb_gender_numeral_subject(root_token, nsubj_token, num):
            continue

        matches.append({
            "root": root_token,
            "nsubj": nsubj_token,
            "num": num,
        })

    return matches


def is_main_verb_gender_numeral_subject(root_token: Token, nsubj_token: Token, num: Token) -> bool:
    if nsubj_token["deprel"] == "nsubj":
        return True
    if root_token["deprel"] == "csubj":
        return False
    return "NumForm" in (num["feats"] or {})


def match_subj_verb_gender_numerals_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_copular_gender_numeral_matches(root))

    return matches


def extract_copular_gender_numeral_matches(root: conllu.TokenTree) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []

    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return matches

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if not is_copular_gender_numeral_subject(root_token, nsubj_token):
            continue

        nums = extract_numeral_children(nsubj)
        if not nums:
            continue

        for num in nums:
            for cop in root.children:
                cop_token = cop.token
                cop_feats = cop_token["feats"] or {}
                if cop_token["upos"] != "AUX":
                    continue
                if cop_token["lemma"] in {"to", "by"}:
                    continue
                if cop_feats.get("Tense") != "Past":
                    continue
                if not agrees_with_gender_numeral_subject(cop_feats, nsubj_feats):
                    continue

                matches.append({
                    "root": root_token,
                    "nsubj": nsubj_token,
                    "num": num,
                    "cop": cop_token,
                })

    return matches


def extract_gender_numeral(tree: conllu.TokenTree) -> Token | None:
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


def is_copular_gender_numeral_subject(root_token: Token, nsubj_token: Token) -> bool:
    if nsubj_token["deprel"] in {"nsubj", "nsubj:pass"}:
        return True
    return root_token["upos"] == "ADV" and nsubj_token["deprel"] == "obl"


def agrees_with_gender_numeral_subject(
        predicate_feats: dict[str, str],
        nsubj_feats: dict[str, str],
) -> bool:
    nsubj_case = nsubj_feats.get("Case")
    return (
        (predicate_feats.get("Gender") == "Neut" and nsubj_case == "Gen")
        or (
            predicate_feats.get("Gender") == nsubj_feats.get("Gender")
            and nsubj_case == "Nom"
        )
    )


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
