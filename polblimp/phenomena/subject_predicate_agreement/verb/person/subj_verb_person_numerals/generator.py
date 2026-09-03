from __future__ import annotations
from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    QUANTIFIER_LEMMAS,
    agrees_with_numeral_subject,
    extract_children,
    is_numeral_or_quantifier,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.verb.person.common import (
    append_aux_clitic,
    change_person,
)


def run_subj_verb_person_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_person(match["root_tree"], morph_dict)

    def transform_1b(_sentence: conllu.TokenList, match: Match) -> bool:
        return append_aux_clitic(match["root"], morph_dict)

    def transform_1c(_sentence: conllu.TokenList, match: Match) -> bool:
        aux = next(child for child in match["root_tree"].children if child.token["deprel"] == "aux")
        return change_person(aux, morph_dict)

    def transform_2a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_person(match["cop_tree"], morph_dict)

    def transform_2b(_sentence: conllu.TokenList, match: Match) -> bool:
        return append_aux_clitic(match["cop"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_1a, "subj_verb_person_numerals__1a"),
            QueryVariant("1b", ("root",), transform_1b, "subj_verb_person_numerals__1b"),
            QueryVariant("1c", ("root",), transform_1c, "subj_verb_person_numerals__1c"),
            QueryVariant("2a", ("cop",), transform_2a, "subj_verb_person_numerals__2a"),
            QueryVariant("2b", ("cop",), transform_2b, "subj_verb_person_numerals__2b"),
        ),
        limit,
    )


def match_subj_verb_person_numerals_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    def extract_match(root: conllu.TokenTree) -> dict[str, Token] | None:
        root_token = root.token
        root_feats = root_token["feats"] or {}

        for nsubj in root.children:
            nsubj_token = nsubj.token
            nsubj_feats = nsubj_token["feats"] or {}

            if nsubj_token["deprel"] != "nsubj":
                continue
            if not agrees_with_numeral_subject(root_feats.get("Number"), nsubj_feats.get("Case")):
                continue

            for num in nsubj.children:
                num_token = num.token
                if num_token["upos"] == "NUM" or (
                        "det" in num_token["deprel"]
                        and num_token["lemma"] in QUANTIFIER_LEMMAS
                ):
                    if not is_person_numeral_subject_present(nsubj_token, num_token):
                        continue
                    return {
                        "root": root_token,
                        "root_tree": root,
                        "nsubj": nsubj_token,
                        "num": num_token,
                    }

        return None

    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if root_feats.get("Tense") not in {"Pres", "Fut"}:
            continue
        if root_feats.get("Person") != "3":
            continue

        match = extract_match(root)
        if match is not None:
            return [match]

    return []


def match_subj_verb_person_numerals_1b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    def extract_match(root: conllu.TokenTree) -> dict[str, Token] | None:
        root_token = root.token
        root_feats = root_token["feats"] or {}

        for nsubj in root.children:
            nsubj_token = nsubj.token
            nsubj_feats = nsubj_token["feats"] or {}

            if nsubj_token["deprel"] != "nsubj":
                continue
            if not agrees_with_numeral_subject(root_feats.get("Number"), nsubj_feats.get("Case")):
                continue

            for num in nsubj.children:
                num_token = num.token
                if num_token["upos"] == "NUM" or (
                        "det" in num_token["deprel"]
                        and num_token["lemma"] in QUANTIFIER_LEMMAS
                ):
                    if not is_person_numeral_subject_past(nsubj_token, num_token):
                        continue
                    return {
                        "root": root_token,
                        "root_tree": root,
                        "nsubj": nsubj_token,
                        "num": num_token,
                    }

        return None

    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if not (root_feats.get("Tense") == "Past" or root_token["lemma"] == "powinien"):
            continue
        if len(extract_children(root, lambda token: token["deprel"] == "aux")) != 0:
            continue

        match = extract_match(root)
        if match is not None:
            return [match]

    return []


def is_person_numeral_subject_present(nsubj: Token, num: Token) -> bool:
    if nsubj["upos"] == "NOUN":
        return True
    if "gov" in num["deprel"]:
        return True
    return nsubj["upos"] == "ADJ" and num["deprel"] == "conj"


def is_person_numeral_subject_past(nsubj: Token, num: Token) -> bool:
    if nsubj["upos"] == "NOUN":
        return True
    return nsubj["upos"] in {"PROPN", "ADJ"} and "gov" in num["deprel"]


def match_subj_verb_person_numerals_1c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    def extract_match(root: conllu.TokenTree) -> dict[str, Token] | None:
        root_token = root.token

        for nsubj in root.children:
            nsubj_token = nsubj.token

            if nsubj_token["upos"] != "NOUN":
                continue
            if nsubj_token["deprel"] != "nsubj":
                continue

            for num in nsubj.children:
                num_token = num.token
                if num_token["upos"] == "NUM" or (
                        "det" in num_token["deprel"]
                        and num_token["lemma"] in QUANTIFIER_LEMMAS
                ):
                    return {
                        "root": root_token,
                        "root_tree": root,
                        "nsubj": nsubj_token,
                        "num": num_token,
                    }

        return None

    for root in token_trees(sentence.to_tree()):
        root_token = root.token

        if root_token["upos"] != "VERB":
            continue
        if root_token["lemma"] == "to":
            continue

        base_match = extract_match(root)
        if base_match is None:
            continue

        nsubj_feats = base_match["nsubj"]["feats"] or {}
        for aux in root.children:
            aux_token = aux.token
            aux_feats = aux_token["feats"] or {}
            if aux_token["deprel"] != "aux":
                continue
            if not agrees_with_numeral_subject(aux_feats.get("Number"), nsubj_feats.get("Case")):
                continue
            return [{
                **base_match,
                "aux": aux_token,
                "aux_tree": aux,
            }]

    return []


def match_subj_verb_person_numerals_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for match in extract_copular_numeral_matches(sentence):
        cop_feats = match["cop"]["feats"] or {}
        if cop_feats.get("Tense") in {"Pres", "Fut"}:
            matches.append(match)

    return matches


def match_subj_verb_person_numerals_2b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for match in extract_copular_numeral_matches(sentence):
        cop_feats = match["cop"]["feats"] or {}
        if cop_feats.get("Tense") == "Past":
            matches.append(match)

    return matches


def extract_copular_numeral_matches(sentence: conllu.TokenList) -> list[dict[str, Token]]:
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

            nums = extract_children(nsubj, is_numeral_or_quantifier)
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
                        "cop_tree": cop,
                    })

    return matches
