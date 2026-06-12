from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, change_morph, match_descendants, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_gender_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(matches: dict[str, Token]) -> bool:
        target_gender = get_target_gender(matches["root"])
        if target_gender is None:
            return False
        if matches["root"]["lemma"] == "powinien" or matches["root"]["xpos"].startswith("winien:"):
            return change_gender(matches["root"], morph_dict, target_gender=target_gender)
        if target_gender == "Masc" and (matches["root"]["feats"] or {}).get("Number") == "Plur":
            return change_plural_to_masculine_personal(matches["root"], morph_dict)
        if target_gender == "Fem":
            return change_gender(matches["root"], morph_dict, target_gender=target_gender)
        return change_gender(matches["root"], morph_dict)

    # Main verb, singular
    def transform_1a(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_1a(sentence))

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_simple__1a",
    )

    # Main verb, plural masculine-personal
    def transform_1b(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_1b(sentence))

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_gender_simple__1b",
    )

    # Main verb, plural non-masculine-personal
    def transform_1c(sentence) -> bool:
        return transform(match_subj_verb_gender_simple_1c(sentence))

    variant_1c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_simple_1c(s) is not None,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_gender_simple__1c",
    )

    variants = [variant_1a, variant_1b, variant_1c]
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


def match_subj_verb_gender_simple(sentence: conllu.TokenList) -> bool:
    return extract_main_verb_gender_match(sentence) is not None


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


def change_plural_to_masculine_personal(token: Token, morph_dict: MorphDictionary) -> bool:
    source_xpos = token["xpos"]
    if source_xpos.endswith(":imperf"):
        target_xpos = "praet:pl:m1:imperf"
    elif source_xpos.endswith(":perf"):
        target_xpos = "praet:pl:m1:perf"
    else:
        print(f"Unknown plural gender tag={source_xpos}, form={token['form']}")
        return False

    return change_morph(token, morph_dict, target_xpos)
