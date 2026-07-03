from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, match_descendants, run_filter_transform, token_trees
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_gender_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(matches: dict[str, Token], target_name: str) -> bool:
        target = matches[target_name]
        target_gender = get_target_gender(target)
        if target_gender is None:
            return False
        return change_gender(target, morph_dict, target_gender=target_gender)

    # Main verb, singular
    def transform_1a(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_1a(sentence), "root")

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_simple__1a",
    )

    # Main verb, plural masculine-personal
    def transform_1b(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_1b(sentence), "root")

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_gender_simple__1b",
    )

    # Main verb, plural non-masculine-personal
    def transform_1c(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_1c(sentence), "root")

    variant_1c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_1c(s) is not None,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_gender_simple__1c",
    )

    # Copular verb, singular
    def transform_2a(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_2a(sentence), "cop")

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_gender_simple__2a",
    )

    # Copular verb, plural masculine-personal
    def transform_2b(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_2b(sentence), "cop")

    variant_2b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_2b(s) is not None,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_gender_simple__2b",
    )

    # Copular verb, plural non-masculine-personal
    def transform_2c(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_2c(sentence), "cop")

    variant_2c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_2c(s) is not None,
        transform_2c,
        limit=limit,
        progress_desc="subj_verb_gender_simple__2c",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_2a, variant_2b, variant_2c]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_gender_simple_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_gender_match(sentence)
    if match is None:
        return None

    root_feats = match["root"]["feats"] or {}
    if root_feats.get("Number") == "Sing":
        return match

    return None


def match_subj_verb_gender_simple_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_gender_match(sentence)
    if match is None:
        return None

    root_feats = match["root"]["feats"] or {}
    if root_feats.get("Number") == "Plur" and is_masculine_personal(match["nsubj"]):
        return match

    return None


def match_subj_verb_gender_simple_1c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    match = extract_main_verb_gender_match(sentence)
    if match is None:
        return None

    root_feats = match["root"]["feats"] or {}
    if root_feats.get("Number") == "Plur" and not is_masculine_personal(match["nsubj"]):
        return match

    return None


def match_subj_verb_gender_simple_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_copular_verb_gender_match(sentence, target_number="Sing")


def match_subj_verb_gender_simple_2b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_copular_verb_gender_match(sentence, target_number="Plur", target_masculine_personal=True)


def match_subj_verb_gender_simple_2c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_copular_verb_gender_match(sentence, target_number="Plur", target_masculine_personal=False)


def extract_main_verb_gender_match(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_feats.get("Number") != "Sing":
        if root_feats.get("Number") != "Plur":
            return None

    root_gender = root_feats.get("Gender")
    root_number = root_feats.get("Number")

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["upos"] != "NOUN":
            continue
        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Gender") != root_gender:
            continue
        if nsubj_feats.get("Number") != root_number:
            continue
        if has_gender_attractor_between(nsubj, root_token):
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
        }

    return None


def extract_copular_verb_gender_match(
        sentence: conllu.TokenList,
        target_number: str | None = None,
        target_masculine_personal: bool | None = None,
) -> dict[str, Token] | None:
    for root in token_trees(sentence.to_tree()):
        match = extract_copular_verb_gender_match_for_root(root, target_number, target_masculine_personal)
        if match is not None:
            return match

    return None


def extract_copular_verb_gender_match_for_root(
        root: conllu.TokenTree,
        target_number: str | None,
        target_masculine_personal: bool | None,
) -> dict[str, Token] | None:
    root_token = root.token

    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return None

    for cop in root.children:
        cop_token = cop.token
        cop_feats = cop_token["feats"] or {}
        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by"}:
            continue
        if cop_feats.get("Number") not in {"Sing", "Plur"}:
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
            if has_gender_attractor_between(nsubj, cop_token):
                continue
            if has_conj_child(nsubj):
                cop_is_plural = cop_feats.get("Number") == "Plur"
                singular_conj_subject_allowed = (
                    root_token["upos"] == "ADJ"
                    or (
                        root_token["upos"] == "VERB"
                        and root_token["lemma"] == "to"
                        and root_token["deprel"] == "root"
                    )
                )
                if cop_is_plural or not singular_conj_subject_allowed:
                    continue
            if (
                    target_masculine_personal is not None
                    and is_masculine_personal(nsubj_token) != target_masculine_personal
            ):
                continue

            return {
                "root": root_token,
                "cop": cop_token,
                "nsubj": nsubj_token,
            }

    return None


def match_subj_verb_gender_simple(sentence: conllu.TokenList) -> bool:
    return (
        extract_main_verb_gender_match(sentence) is not None
        or extract_copular_verb_gender_match(sentence) is not None
    )


def has_conj_child(tree: conllu.TokenTree) -> bool:
    return any(child.token["deprel"] == "conj" for child in tree.children)


def has_gender_attractor_between(nsubj: conllu.TokenTree, root_token: Token) -> bool:
    nsubj_token = nsubj.token
    nsubj_id = nsubj_token["id"]
    root_id = root_token["id"]
    if not isinstance(nsubj_id, int) or not isinstance(root_id, int):
        return False

    nsubj_feats = nsubj_token["feats"] or {}
    root_feats = root_token["feats"] or {}
    root_number = root_feats.get("Number")
    root_gender = root_feats.get("Gender")
    nsubj_is_masc_personal = is_masculine_personal(nsubj_token)

    lower_id = min(nsubj_id, root_id)
    upper_id = max(nsubj_id, root_id)
    attractor_deprels = {"nmod", "nmod:poss", "nmod:arg", "xcomp", "conj", "nummod"}
    attractors = match_descendants(
        nsubj,
        lambda token: (
            token["deprel"] in attractor_deprels
            and isinstance(token["id"], int)
            and lower_id < token["id"] < upper_id
            and (
                (root_number == "Sing" and (token["feats"] or {}).get("Gender") != root_gender)
                or (root_number == "Plur" and is_masculine_personal(token) != nsubj_is_masc_personal)
            )
        ),
    )
    return len(attractors) != 0


def is_masculine_personal(token: Token) -> bool:
    feats = token["feats"] or {}
    return feats.get("SubGender") == "Masc1" or feats.get("Animacy") == "Hum"


def get_target_gender(token: Token) -> str | None:
    feats = token["feats"] or {}
    gender = feats.get("Gender")
    number = feats.get("Number")

    if number == "Plur":
        return "Fem" if is_masculine_personal(token) else "Masc"
    if gender == "Masc":
        return "Fem"
    if gender in {"Fem", "Neut"}:
        return "Masc"

    return None
