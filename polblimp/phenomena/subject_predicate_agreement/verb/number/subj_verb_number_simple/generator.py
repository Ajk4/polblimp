from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    change_number,
    match_descendants,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.verb.number.common import change_number_with_aux_clitic


def run_subj_verb_number_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_root(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["root"], morph_dict)

    def transform_1c(sentence: conllu.TokenList, match: Match) -> bool:
        auxclitic = extract_aux_clitic(match["root_tree"])
        assert auxclitic is not None
        return change_number_with_aux_clitic(
            sentence,
            match["root"],
            auxclitic,
            (match["nsubj"]["feats"] or {})["Person"],
            morph_dict,
        )

    def transform_2a(_sentence: conllu.TokenList, match: Match) -> bool:
        aux = next(child.token for child in match["root_tree"].children if child.token["deprel"] == "aux")
        return change_number(aux, morph_dict)

    def transform_2b(_sentence: conllu.TokenList, match: Match) -> bool:
        aux = next(child.token for child in match["root_tree"].children if child.token["deprel"] == "aux")
        return change_number(aux, morph_dict) and change_number(match["root"], morph_dict)

    def transform_3a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_number(match["cop"], morph_dict)

    def transform_3b(sentence: conllu.TokenList, match: Match) -> bool:
        auxclitic = extract_aux_clitic(match["root_tree"])
        assert auxclitic is not None
        return change_number_with_aux_clitic(
            sentence,
            match["cop"],
            auxclitic,
            (match["nsubj"]["feats"] or {})["Person"],
            morph_dict,
        )

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_root, "subj_verb_number_simple__1a"),
            QueryVariant("1b", ("root",), transform_root, "subj_verb_number_simple__1b"),
            QueryVariant("1c", ("root", "nsubj"), transform_1c, "subj_verb_number_simple__1c"),
            QueryVariant("2a", ("root",), transform_2a, "subj_verb_number_simple__2a"),
            QueryVariant("2b", ("root",), transform_2b, "subj_verb_number_simple__2b"),
            QueryVariant("3a", ("cop",), transform_3a, "subj_verb_number_simple__3a"),
            QueryVariant("3b", ("root", "cop", "nsubj"), transform_3b, "subj_verb_number_simple__3b"),
        ),
        limit,
    )


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
        if cop_token["lemma"] in {"to", "by", "niech"}:
            continue
        if cop_number is None:
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
