from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    change_aux_clitic_number,
    change_number,
    match_descendants,
    run_filter_transform,
)
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_number_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_number_simple_1a(sentence)
        return change_number(matches["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_simple_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_number_simple__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_number_simple_1b(sentence)
        return change_number(matches["root"], morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_simple_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_number_simple__1b",
    )

    # Main verb, compound future
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_number_simple_2a(sentence)
        return change_number(matches["aux"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_simple_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_number_simple__2a",
    )

    def transform_2b(sentence) -> bool:
        matches = match_subj_verb_number_simple_2b(sentence)
        return change_number(matches["aux"], morph_dict) and change_number(matches["root"], morph_dict)

    variant_2b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_simple_2b(s) is not None,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_number_simple__2b",
    )

    # Copular auxiliary verb
    def transform_3a(sentence) -> bool:
        matches = match_subj_verb_number_simple_3a(sentence)
        return change_number(matches["cop"], morph_dict)

    variant_3a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_simple_3a(s) is not None,
        transform_3a,
        limit=limit,
        progress_desc="subj_verb_number_simple__3a",
    )

    def transform_3b(sentence) -> bool:
        matches = match_subj_verb_number_simple_3b(sentence)
        return (
            change_number(matches["cop"], morph_dict)
            and change_aux_clitic_number(matches["cop"], matches["auxclitic"], morph_dict)
        )

    variant_3b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_number_simple_3b(s) is not None,
        transform_3b,
        limit=limit,
        progress_desc="subj_verb_number_simple__3b",
    )

    variants = [variant_1a, variant_1b, variant_2a, variant_2b, variant_3a, variant_3b]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_number_simple_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_number_match(sentence, reference="root")
    if match is None:
        return None

    nsubj_feats = match["nsubj"]["feats"] or {}
    if nsubj_feats.get("Person") not in {"1", "2"}:
        return match

    return None


def match_subj_verb_number_simple_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_number_match(sentence, reference="root")
    if match is None:
        return None

    root_feats = match["root"]["feats"] or {}
    nsubj_feats = match["nsubj"]["feats"] or {}
    if nsubj_feats.get("Person") not in {"1", "2"}:
        return None
    if root_feats.get("Tense") in {"Pres", "Fut"}:
        return match

    return None


def match_subj_verb_number_simple_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_number_match(sentence, reference="aux")
    if match is None:
        return None

    root_feats = match["root"]["feats"] or {}
    if root_feats.get("VerbForm") != "Fin":
        return match

    return None


def match_subj_verb_number_simple_2b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_number_match(sentence, reference="aux")
    if match is None:
        return None

    root_feats = match["root"]["feats"] or {}
    if root_feats.get("VerbForm") == "Fin":
        return match

    return None


def match_subj_verb_number_simple_3a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_copular_number_match(sentence)
    if match is None:
        return None

    cop_feats = match["cop"]["feats"] or {}
    nsubj_feats = match["nsubj"]["feats"] or {}
    if nsubj_feats.get("Person") not in {"1", "2"}:
        return match
    if cop_feats.get("Tense") in {"Pres", "Fut"}:
        return match

    return None


def match_subj_verb_number_simple_3b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_copular_number_match(sentence)
    if match is None:
        return None

    cop_feats = match["cop"]["feats"] or {}
    nsubj_feats = match["nsubj"]["feats"] or {}
    if cop_feats.get("Tense") != "Past":
        return None
    if nsubj_feats.get("Person") not in {"1", "2"}:
        return None

    root = sentence.to_tree()
    for auxclitic in root.children:
        if auxclitic.token["deprel"] == "aux:clitic":
            return {
                **match,
                "auxclitic": auxclitic.token,
            }

    return None


def extract_main_verb_number_match(
        sentence: conllu.TokenList,
        reference: str,
) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None

    reference_token = root_token
    aux_token = None
    if reference == "aux":
        if root_token["lemma"] == "to":
            return None
        for aux in root.children:
            if aux.token["deprel"] == "aux":
                aux_token = aux.token
                reference_token = aux_token
                break
        if aux_token is None:
            return None

    reference_feats = reference_token["feats"] or {}
    reference_number = reference_feats.get("Number")

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue
        if nsubj_feats.get("Number") != reference_number:
            continue
        if has_conj_child(nsubj):
            continue
        if has_attractor_between(nsubj, reference_token, reference_number):
            continue

        match = {
            "root": root_token,
            "nsubj": nsubj_token,
        }
        if aux_token is not None:
            match["aux"] = aux_token
        return match

    return None


def extract_copular_number_match(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return None

    for cop in root.children:
        cop_token = cop.token
        cop_feats = cop_token["feats"] or {}
        cop_number = cop_feats.get("Number")

        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by"}:
            continue

        for nsubj in root.children:
            nsubj_token = nsubj.token
            nsubj_feats = nsubj_token["feats"] or {}

            if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
                continue
            if nsubj_feats.get("Case") != "Nom":
                continue
            if nsubj_feats.get("Number") != cop_number:
                continue
            if has_conj_child(nsubj):
                continue
            if has_attractor_between(nsubj, cop_token, cop_number):
                continue

            return {
                "root": root_token,
                "nsubj": nsubj_token,
                "cop": cop_token,
            }

    return None


def has_attractor_between(
        nsubj: conllu.TokenTree,
        target_token: Token,
        reference_number: str | None,
) -> bool:
    nsubj_id = nsubj.token["id"]
    target_id = target_token["id"]
    if not isinstance(nsubj_id, int) or not isinstance(target_id, int):
        return False

    attractor_deprels = {"nmod", "nmod:poss", "nmod:arg", "xcomp", "nummod", "conj"}

    lower_id = min(nsubj_id, target_id)
    upper_id = max(nsubj_id, target_id)
    attractors = match_descendants(
        nsubj,
        lambda token: (
            token["deprel"] in attractor_deprels
            and (token["feats"] or {}).get("Number") != reference_number
            and isinstance(token["id"], int)
            and lower_id < token["id"] < upper_id
        ),
    )
    return len(attractors) != 0


def has_conj_child(nsubj: conllu.TokenTree) -> bool:
    for child in nsubj.children:
        if child.token["deprel"] == "conj":
            return True

    return False
