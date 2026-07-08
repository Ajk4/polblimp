from __future__ import annotations
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    QUANTIFIER_LEMMAS,
    agrees_with_numeral_subject,
    extract_children,
    is_numeral_or_quantifier,
    run_filter_transform,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.common import (
    append_aux_clitic,
    change_person,
)


def run_subj_verb_person_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_person_numerals_1a(sentence)
        return change_person(matches[0]["root_tree"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_person_numerals_1a(s)),
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_person_numerals__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_person_numerals_1b(sentence)
        return append_aux_clitic(matches[0]["root"], morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_person_numerals_1b(s)),
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_person_numerals__1b",
    )

    def transform_1c(sentence) -> bool:
        matches = match_subj_verb_person_numerals_1c(sentence)
        return change_person(matches[0]["aux_tree"], morph_dict)

    variant_1c = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_person_numerals_1c(s)),
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_person_numerals__1c",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_person_numerals_2a(sentence)
        return change_person(matches[0]["cop_tree"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_person_numerals_2a(s)),
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_person_numerals__2a",
    )

    def transform_2b(sentence) -> bool:
        matches = match_subj_verb_person_numerals_2b(sentence)
        return append_aux_clitic(matches[0]["cop"], morph_dict)

    variant_2b = run_filter_transform(
        sentences,
        lambda s: bool(match_subj_verb_person_numerals_2b(s)),
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_person_numerals__2b",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a, variant_2b]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


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
