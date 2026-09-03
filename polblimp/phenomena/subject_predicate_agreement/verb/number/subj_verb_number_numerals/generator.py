from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    QUANTIFIER_LEMMAS,
    agrees_with_numeral_subject,
    change_number,
    extract_children,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms


def run_subj_verb_number_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["root"], morph_dict)

    def transform_1b(_sentence: conllu.TokenList, match: Match) -> bool:
        aux = next(child.token for child in match["root_tree"].children if child.token["deprel"] == "aux")
        return change_number(aux, morph_dict)

    def transform_1c(_sentence: conllu.TokenList, match: Match) -> bool:
        root_feats = match["root"]["feats"] or {}
        aux = next(child.token for child in match["root_tree"].children if child.token["deprel"] == "aux")
        if not change_number(aux, morph_dict):
            return False
        if root_feats.get("VerbForm") == "Fin":
            return change_number(match["root"], morph_dict)
        return True

    def transform_2a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["cop"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_1a, "subj_verb_number_numerals__1a"),
            QueryVariant("1b", ("root",), transform_1b, "subj_verb_number_numerals__1b"),
            QueryVariant("1c", ("root",), transform_1c, "subj_verb_number_numerals__1c"),
            QueryVariant("2a", ("cop",), transform_2a, "subj_verb_number_numerals__2a"),
        ),
        limit,
    )


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
