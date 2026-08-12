from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_adjectival_gender_cop(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def match_for_generation(sentence: conllu.TokenList) -> dict[str, Token] | None:
        match = match_subj_adjectival_gender_cop(sentence)
        if match is None:
            return None

        root_feats = match["root"]["feats"] or {}
        cop_feats = match["cop"]["feats"] or {}
        if root_feats.get("Gender") is None or cop_feats.get("Gender") is None:
            return None
        if root_feats.get("Number") == "Sing" and root_feats.get("Gender") != cop_feats.get("Gender"):
            return None
        if get_target_gender(match["root"]) is None:
            return None
        return match

    def transform(sentence: conllu.TokenList) -> bool:
        matches = match_for_generation(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"

        target_gender = get_target_gender(matches["root"])
        assert target_gender is not None

        return (
            change_gender(matches["root"], morph_dict, target_gender=target_gender)
            and change_gender(matches["cop"], morph_dict, target_gender=target_gender)
        )

    return run_filter_transform(
        sentences,
        lambda s: match_for_generation(s) is not None,
        transform,
        limit=limit,
        progress_desc="subj_adjectival_gender_cop",
    )


def match_subj_adjectival_gender_cop(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["upos"] != "ADJ":
        return None
    if root_token["deprel"] != "root":
        return None

    nsubj_token = None
    for child in root.children:
        child_token = child.token
        child_feats = child_token["feats"] or {}
        if child_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        if child_feats.get("Case") != "Nom":
            continue
        if child_feats.get("Person") in {"1", "2"}:
            continue
        nsubj_token = child_token
        break

    if nsubj_token is None:
        return None

    for child in root.children:
        child_token = child.token
        child_feats = child_token["feats"] or {}
        if child_token["upos"] != "AUX":
            continue
        if child_token.get("lemma") in {"to", "by"}:
            continue
        if child_feats.get("Tense") != "Past":
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
            "cop": child_token,
        }

    return None


def get_target_gender(token: Token) -> str | None:
    feats = token["feats"] or {}
    gender = feats.get("Gender")
    if feats.get("Number") == "Plur":
        masculine_personal = feats.get("SubGender") == "Masc1" or feats.get("Animacy") == "Hum"
        return "Fem" if masculine_personal else "Masc"
    if gender == "Masc":
        return "Fem"
    if gender in {"Fem", "Neut"}:
        return "Masc"
    return None
