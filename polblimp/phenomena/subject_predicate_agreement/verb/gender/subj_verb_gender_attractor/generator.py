from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, match_descendants, run_filter_transform, token_trees
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_simple.generator import (
    has_conj_child,
    is_masculine_personal,
)


def run_subj_verb_gender_attractor(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(matches: list[dict[str, Token]], target_name: str) -> bool:
        target = matches[0][target_name]
        target_gender = get_target_gender(target, matches[0]["attractor"])
        if target_gender is None:
            return False
        return change_gender(target, morph_dict, target_gender=target_gender)

    # Main verb, singular
    def transform_1a(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_1a(sentence), "root")

    variant_1a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_gender_attractor_1a(s)) != 0,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__1a",
    )

    # Main verb, plural masculine-personal
    def transform_1b(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_1b(sentence), "root")

    variant_1b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_gender_attractor_1b(s)) != 0,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__1b",
    )

    # Main verb, plural non-masculine-personal
    def transform_1c(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_1c(sentence), "root")

    variant_1c = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_gender_attractor_1c(s)) != 0,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__1c",
    )

    # Copular verb, singular
    def transform_2a(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_2a(sentence), "cop")

    variant_2a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_gender_attractor_2a(s)) != 0,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__2a",
    )

    # Copular verb, plural masculine-personal
    def transform_2b(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_2b(sentence), "cop")

    variant_2b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_gender_attractor_2b(s)) != 0,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__2b",
    )

    # Copular verb, plural non-masculine-personal
    def transform_2c(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_2c(sentence), "cop")

    variant_2c = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_gender_attractor_2c(s)) != 0,
        transform_2c,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__2c",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a, variant_2b, variant_2c]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_gender_attractor_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence)
        if (match["root"]["feats"] or {}).get("Number") == "Sing"
    ]


def match_subj_verb_gender_attractor_1b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence)
        if (match["root"]["feats"] or {}).get("Number") == "Plur"
        and is_masculine_personal(match["nsubj"])
    ]


def match_subj_verb_gender_attractor_1c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_main_verb_attractor_matches(sentence)
        if (match["root"]["feats"] or {}).get("Number") == "Plur"
        and not is_masculine_personal(match["nsubj"])
    ]


def match_subj_verb_gender_attractor_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return extract_copular_attractor_matches(sentence, target_number="Sing")


def match_subj_verb_gender_attractor_2b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return extract_copular_attractor_matches(sentence, target_number="Plur", target_masculine_personal=True)


def match_subj_verb_gender_attractor_2c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return extract_copular_attractor_matches(sentence, target_number="Plur", target_masculine_personal=False)


def extract_main_verb_attractor_matches(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_main_verb_attractor_matches_for_root(root))

    return matches


def extract_main_verb_attractor_matches_for_root(root: conllu.TokenTree) -> list[dict[str, Token]]:
    root_token = root.token
    root_feats = root_token["feats"] or {}
    matches = []

    if root_token["upos"] != "VERB":
        return matches

    root_gender = root_feats.get("Gender")
    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue
        if nsubj_feats.get("Gender") != root_gender:
            continue
        if has_conj_child(nsubj):
            continue

        for attractor in find_gender_attractors_between(root, nsubj_token, root_token):
            matches.append({
                "root": root_token,
                "nsubj": nsubj_token,
                "attractor": attractor,
            })

    return matches


def extract_copular_attractor_matches(
        sentence: conllu.TokenList,
        target_number: str | None,
        target_masculine_personal: bool | None = None,
) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_copular_attractor_matches_for_root(root, target_number, target_masculine_personal))

    return matches


def extract_copular_attractor_matches_for_root(
        root: conllu.TokenTree,
        target_number: str | None,
        target_masculine_personal: bool | None,
) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []

    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return matches

    for cop in root.children:
        cop_token = cop.token
        cop_feats = cop_token["feats"] or {}
        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by"}:
            continue
        if target_number is not None and cop_feats.get("Number") != target_number:
            continue

        cop_gender = cop_feats.get("Gender")
        for nsubj in root.children:
            nsubj_token = nsubj.token
            nsubj_feats = nsubj_token["feats"] or {}
            if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
                continue
            if nsubj_feats.get("Case") != "Nom":
                continue
            if nsubj_feats.get("Gender") != cop_gender:
                continue
            if has_conj_child(nsubj):
                continue
            if (
                    target_masculine_personal is not None
                    and is_masculine_personal(nsubj_token) != target_masculine_personal
            ):
                continue

            for attractor in find_gender_attractors_between(root, nsubj_token, cop_token):
                matches.append({
                    "root": root_token,
                    "cop": cop_token,
                    "nsubj": nsubj_token,
                    "attractor": attractor,
                })

    return matches


def find_gender_attractors_between(
        root: conllu.TokenTree,
        nsubj_token: Token,
        target_token: Token,
) -> list[Token]:
    nsubj_id = nsubj_token["id"]
    target_id = target_token["id"]
    if not isinstance(nsubj_id, int) or not isinstance(target_id, int):
        return []

    lower_id = min(nsubj_id, target_id)
    upper_id = max(nsubj_id, target_id)
    target_feats = target_token["feats"] or {}
    target_number = target_feats.get("Number")
    attractors = match_descendants(
        root,
        lambda token: (
            is_noun_or_pronoun(token)
            and isinstance(token["id"], int)
            and lower_id < token["id"] < upper_id
            and (
                (
                    target_number == "Sing"
                    and (token["feats"] or {}).get("Gender") != target_feats.get("Gender")
                )
                or (
                    target_number == "Plur"
                    and is_masculine_personal(token) != is_masculine_personal(nsubj_token)
                )
            )
        ),
    )

    return [
        attractor
        for attractor in attractors
        if not has_intervening_noun_or_pronoun(root, attractor, target_token)
    ]


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


def is_noun_or_pronoun(token: Token) -> bool:
    xpos = token.get("xpos") or ""
    return "subst" in xpos or "ppron" in xpos


def get_target_gender(target: Token, attractor: Token) -> str | None:
    target_feats = target["feats"] or {}
    if target_feats.get("Number") == "Sing":
        return (attractor["feats"] or {}).get("Gender")
    if target_feats.get("Number") == "Plur":
        return "Fem" if is_masculine_personal(target) else "Masc"
    return None
