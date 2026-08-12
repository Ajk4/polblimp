from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    QUANTIFIER_LEMMAS,
    agrees_with_numeral_subject,
    change_number,
    extract_children,
    run_filter_transform,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_number_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_number_numerals_1a(sentence)
        return change_number(matches[0]["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_number_numerals_1a(s)),
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
        return change_number(matches[0]["cop"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_number_numerals_2a(s)),
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_number_numerals__2a",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_number_numerals_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if any(child.token["deprel"] == "aux" for child in root.children):
            continue
        if root_feats.get("Tense") not in {"Pres", "Fut", "Past"}:
            continue

        matches.extend(extract_main_verb_number_numeral_matches(root, sentence))

    return matches


def match_subj_verb_number_numerals_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if root_token["lemma"] == "to":
            continue
        if root_feats.get("VerbForm") == "Fin":
            continue

        base_match = extract_main_verb_number_numeral_base_match(root, sentence)
        if base_match is None:
            continue

        match = extract_aux_number_numeral_match(root, base_match)
        if match is not None:
            return match

    return None


def match_subj_verb_number_numerals_1c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if root_token["lemma"] == "to":
            continue
        if root_feats.get("VerbForm") != "Fin":
            continue

        base_match = extract_main_verb_number_numeral_base_match(root, sentence)
        if base_match is None:
            continue

        match = extract_aux_number_numeral_match(root, base_match)
        if match is not None:
            return match

    return None


def match_subj_verb_number_numerals_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return extract_copular_number_numeral_matches(sentence)


def match_subj_verb_number_numerals_2b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return None


def extract_main_verb_number_numeral_match(
        root: conllu.TokenTree,
        sentence: conllu.TokenList,
) -> dict[str, Token] | None:
    matches = extract_main_verb_number_numeral_matches(root, sentence)
    return matches[0] if matches else None


def extract_main_verb_number_numeral_matches(
        root: conllu.TokenTree,
        sentence: conllu.TokenList,
) -> list[dict[str, Token]]:
    root_feats = root.token["feats"] or {}
    matches = []

    for match in extract_main_verb_number_numeral_base_matches(root, sentence):
        nsubj_feats = match["nsubj"]["feats"] or {}
        if agrees_with_numeral_subject(root_feats.get("Number"), nsubj_feats.get("Case")):
            matches.append(match)

    return matches


def extract_main_verb_number_numeral_base_match(
        root: conllu.TokenTree,
        sentence: conllu.TokenList,
) -> dict[str, Token] | None:
    matches = extract_main_verb_number_numeral_base_matches(root, sentence)
    return matches[0] if matches else None


def extract_main_verb_number_numeral_base_matches(
        root: conllu.TokenTree,
        sentence: conllu.TokenList,
) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []

    for nsubj in root.children:
        nsubj_token = nsubj.token

        if nsubj_token["deprel"] != "nsubj":
            continue

        nums = extract_children(nsubj, is_number_numeral_or_quantifier)
        num = nums[0] if nums else None
        if num is None:
            continue
        if not is_number_numeral_subject(nsubj_token, num):
            continue

        matches.append({
            "root": root_token,
            "nsubj": nsubj_token,
            "num": num,
        })

    return matches


def extract_aux_number_numeral_match(
        root: conllu.TokenTree,
        base_match: dict[str, Token],
) -> dict[str, Token] | None:
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


def is_number_numeral_subject(token: Token, num: Token) -> bool:
    if token["upos"] == "NOUN":
        return True

    return token["upos"] == "PROPN" and "gov" in num["deprel"]


def is_number_numeral_or_quantifier(token: Token) -> bool:
    return token["upos"] == "NUM" or (
        "det" in token["deprel"] and token["lemma"] in QUANTIFIER_LEMMAS
    )


def extract_copular_number_numeral_matches(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []

    for root in token_trees(sentence.to_tree()):
        root_token = root.token

        if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
            continue

        for nsubj in root.children:
            nsubj_token = nsubj.token
            nsubj_feats = nsubj_token["feats"] or {}
            if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
                continue

            nums = extract_children(nsubj, is_number_numeral_or_quantifier)
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
                    if not agrees_with_numeral_subject(cop_feats.get("Number"), nsubj_feats.get("Case")):
                        continue
                    matches.append({
                        "root": root_token,
                        "nsubj": nsubj_token,
                        "num": num,
                        "cop": cop_token,
                    })

    return matches
