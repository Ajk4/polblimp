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
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_simple.generator import (
    extract_aux_clitic,
    has_conj_child,
)


def run_subj_verb_number_attractor(
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

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_root, "subj_verb_number_attractor__1a"),
            QueryVariant("1b", ("root",), transform_root, "subj_verb_number_attractor__1b"),
            QueryVariant("1c", ("root", "nsubj"), transform_1c, "subj_verb_number_attractor__1c"),
            QueryVariant("2a", ("root",), transform_2a, "subj_verb_number_attractor__2a"),
            QueryVariant("2b", ("root",), transform_2b, "subj_verb_number_attractor__2b"),
            QueryVariant("3a", ("cop",), transform_3a, "subj_verb_number_attractor__3a"),
        ),
        limit,
    )


def match_subj_verb_number_attractor_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence, reference="root")
        if (match["nsubj"]["feats"] or {}).get("Person") not in {"1", "2"}
    ]


def match_subj_verb_number_attractor_1b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence, reference="root")
        if (match["nsubj"]["feats"] or {}).get("Person") in {"1", "2"}
        and (match["root"]["feats"] or {}).get("Tense") in {"Pres", "Fut"}
    ]


def match_subj_verb_number_attractor_1c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        auxclitic = extract_aux_clitic(root)
        if auxclitic is None:
            continue
        for match in extract_main_verb_attractor_matches_for_root(root, reference="root"):
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


def match_subj_verb_number_attractor_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence, reference="aux")
        if (match["root"]["feats"] or {}).get("VerbForm") != "Fin"
    ]


def match_subj_verb_number_attractor_2b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence, reference="aux")
        if (match["root"]["feats"] or {}).get("VerbForm") == "Fin"
    ]


def match_subj_verb_number_attractor_3a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_copular_attractor_matches(sentence)
        if (match["nsubj"]["feats"] or {}).get("Person") not in {"1", "2"}
        or (
            (match["nsubj"]["feats"] or {}).get("Person") in {"1", "2"}
            and (match["cop"]["feats"] or {}).get("Tense") in {"Pres", "Fut"}
        )
    ]


def extract_main_verb_attractor_matches(
        sentence: conllu.TokenList,
        reference: str,
) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_main_verb_attractor_matches_for_root(root, reference))

    return matches


def extract_main_verb_attractor_matches_for_root(
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
        if has_instrumental_z_descendant(nsubj):
            continue

        attractor = find_number_attractor_between(root, nsubj_token, reference_token, reference_number)
        if attractor is None:
            continue

        match = {
            "root": root_token,
            "nsubj": nsubj_token,
            "attractor": attractor,
        }
        if aux_token is not None:
            match["aux"] = aux_token
        matches.append(match)

    return matches


def extract_copular_attractor_matches(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_copular_attractor_matches_for_root(root))

    return matches


def extract_copular_attractor_matches_for_root(root: conllu.TokenTree) -> list[dict[str, Token]]:
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
            if nsubj_feats.get("Number") != cop_number:
                continue
            if has_conj_child(nsubj):
                continue
            if has_instrumental_z_descendant(nsubj):
                continue

            attractor = find_number_attractor_between(root, nsubj_token, cop_token, cop_number)
            if attractor is None:
                continue

            matches.append({
                "root": root_token,
                "nsubj": nsubj_token,
                "cop": cop_token,
                "attractor": attractor,
            })

    return matches


def find_number_attractor_between(
        root: conllu.TokenTree,
        nsubj_token: Token,
        target_token: Token,
        reference_number: str | None,
) -> Token | None:
    nsubj_id = nsubj_token["id"]
    target_id = target_token["id"]
    if not isinstance(nsubj_id, int) or not isinstance(target_id, int):
        return None

    lower_id = min(nsubj_id, target_id)
    upper_id = max(nsubj_id, target_id)
    attractors = match_descendants(
        root,
        lambda token: (
            is_noun_or_pronoun(token)
            and (token["feats"] or {}).get("Number") not in {reference_number, None}
            and (reference_number == "Sing" or (token["feats"] or {}).get("Number") != "Ptan")
            and isinstance(token["id"], int)
            and lower_id < token["id"] < upper_id
        ),
    )

    for attractor in attractors:
        if has_intervening_noun_or_pronoun(root, attractor, target_token):
            continue
        return attractor

    return None


def has_intervening_noun_or_pronoun(
        root: conllu.TokenTree,
        attractor: Token,
        target_token: Token,
) -> bool:
    attractor_id = attractor["id"]
    target_id = target_token["id"]
    if not isinstance(attractor_id, int) or not isinstance(target_id, int):
        return False

    lower_id = min(attractor_id, target_id)
    upper_id = max(attractor_id, target_id)
    intervening = match_descendants(
        root,
        lambda token: (
            token is not attractor
            and is_noun_or_pronoun(token)
            and isinstance(token["id"], int)
            and lower_id < token["id"] < upper_id
        ),
    )
    return len(intervening) != 0


def has_instrumental_z_descendant(nsubj: conllu.TokenTree) -> bool:
    for descendant in token_tree_descendants(nsubj):
        descendant_token = descendant.token
        descendant_feats = descendant_token["feats"] or {}
        if descendant_feats.get("Case") != "Ins":
            continue
        if not is_noun_or_pronoun(descendant_token):
            continue
        for child in descendant.children:
            if child.token["lemma"] == "z":
                return True

    return False


def token_tree_descendants(tree: conllu.TokenTree) -> list[conllu.TokenTree]:
    descendants = []
    for child in tree.children:
        descendants.append(child)
        descendants.extend(token_tree_descendants(child))
    return descendants


def is_noun_or_pronoun(token: Token) -> bool:
    xpos = token.get("xpos") or ""
    return "subst" in xpos or "ppron" in xpos
