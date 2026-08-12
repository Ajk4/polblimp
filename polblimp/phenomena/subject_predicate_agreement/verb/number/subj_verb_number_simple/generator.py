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
    token_trees,
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
        return change_number(matches[0]["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_1a(s)) != 0,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_number_simple__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_number_simple_1b(sentence)
        return change_number(matches[0]["root"], morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_1b(s)) != 0,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_number_simple__1b",
    )

    def transform_1c(sentence) -> bool:
        matches = match_subj_verb_number_simple_1c(sentence)
        return (
            change_number(matches[0]["root"], morph_dict)
            and change_aux_clitic_number(matches[0]["root"], matches[0]["auxclitic"], morph_dict)
        )

    variant_1c = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_1c(s)) != 0,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_number_simple__1c",
    )

    # Main verb, compound future
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_number_simple_2a(sentence)
        return change_number(matches[0]["aux"], morph_dict)

    variant_2a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_2a(s)) != 0,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_number_simple__2a",
    )

    def transform_2b(sentence) -> bool:
        matches = match_subj_verb_number_simple_2b(sentence)
        return change_number(matches[0]["aux"], morph_dict) and change_number(matches[0]["root"], morph_dict)

    variant_2b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_2b(s)) != 0,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_number_simple__2b",
    )

    # Copular auxiliary verb
    def transform_3a(sentence) -> bool:
        matches = match_subj_verb_number_simple_3a(sentence)
        return change_number(matches[0]["cop"], morph_dict)

    variant_3a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_3a(s)) != 0,
        transform_3a,
        limit=limit,
        progress_desc="subj_verb_number_simple__3a",
    )

    def transform_3b(sentence) -> bool:
        matches = match_subj_verb_number_simple_3b(sentence)
        return (
            change_number(matches[0]["cop"], morph_dict)
            and change_aux_clitic_number(matches[0]["cop"], matches[0]["auxclitic"], morph_dict)
        )

    variant_3b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_number_simple_3b(s)) != 0,
        transform_3b,
        limit=limit,
        progress_desc="subj_verb_number_simple__3b",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a, variant_2b, variant_3a, variant_3b]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_number_simple_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_number_matches(sentence, reference="root")
        if (match["nsubj"]["feats"] or {}).get("Person") not in {"1", "2"}
    ]


def match_subj_verb_number_simple_1b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_number_matches(sentence, reference="root")
        if (match["nsubj"]["feats"] or {}).get("Person") in {"1", "2"}
        and (match["root"]["feats"] or {}).get("Tense") in {"Pres", "Fut"}
    ]


def match_subj_verb_number_simple_1c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        auxclitic = extract_aux_clitic(root)
        if auxclitic is None:
            continue
        for match in extract_main_verb_number_matches_for_root(root, reference="root"):
            root_feats = match["root"]["feats"] or {}
            nsubj_feats = match["nsubj"]["feats"] or {}
            if nsubj_feats.get("Person") not in {"1", "2"}:
                continue
            if root_feats.get("Tense") != "Past" and match["root"]["lemma"] != "powinien":
                continue
            matches.append({
                **match,
                "auxclitic": auxclitic,
            })

    return matches


def match_subj_verb_number_simple_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_number_matches(sentence, reference="aux")
        if (match["root"]["feats"] or {}).get("VerbForm") != "Fin"
    ]


def match_subj_verb_number_simple_2b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_number_matches(sentence, reference="aux")
        if (match["root"]["feats"] or {}).get("VerbForm") == "Fin"
    ]


def match_subj_verb_number_simple_3a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_copular_number_matches(sentence)
        if (match["nsubj"]["feats"] or {}).get("Person") not in {"1", "2"}
        or (
            (match["nsubj"]["feats"] or {}).get("Person") in {"1", "2"}
            and (match["cop"]["feats"] or {}).get("Tense") in {"Pres", "Fut"}
        )
    ]


def match_subj_verb_number_simple_3b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        auxclitic = extract_aux_clitic(root)
        if auxclitic is None:
            continue
        for match in extract_copular_number_matches_for_root(root):
            cop_feats = match["cop"]["feats"] or {}
            nsubj_feats = match["nsubj"]["feats"] or {}
            if cop_feats.get("Tense") != "Past":
                continue
            if nsubj_feats.get("Person") not in {"1", "2"}:
                continue
            matches.append({
                **match,
                "auxclitic": auxclitic,
            })

    return matches


def extract_main_verb_number_matches(
        sentence: conllu.TokenList,
        reference: str,
) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_main_verb_number_matches_for_root(root, reference))

    return matches


def extract_main_verb_number_matches_for_root(
        root: conllu.TokenTree,
        reference: str,
) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []

    if root_token["upos"] != "VERB":
        return matches
    if reference == "root" and any(child.token["deprel"] == "aux" for child in root.children):
        return matches

    reference_token = root_token
    aux_token = None
    if reference == "aux":
        if root_token["lemma"] == "to":
            return matches
        for aux in root.children:
            if aux.token["deprel"] == "aux":
                aux_token = aux.token
                reference_token = aux_token
                break
        if aux_token is None:
            return matches

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
        matches.append(match)

    return matches


def extract_copular_number_matches(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_copular_number_matches_for_root(root))

    return matches


def extract_copular_number_matches_for_root(root: conllu.TokenTree) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []

    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return matches

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
            if has_conj_child(nsubj):
                continue
            if has_attractor_between(nsubj, cop_token, cop_number):
                continue

            matches.append({
                "root": root_token,
                "nsubj": nsubj_token,
                "cop": cop_token,
            })

    return matches


def extract_aux_clitic(root: conllu.TokenTree) -> Token | None:
    for child in root.children:
        if child.token["deprel"] == "aux:clitic":
            return child.token

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

    lower_id = min(nsubj_id, target_id)
    upper_id = max(nsubj_id, target_id)
    attractors = match_descendants(
        nsubj,
        lambda token: (
            is_noun_or_pronoun(token)
            and (token["feats"] or {}).get("Number") not in {reference_number, None}
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


def is_noun_or_pronoun(token: Token) -> bool:
    xpos = token.get("xpos") or ""
    return "subst" in xpos or "ppron" in xpos
