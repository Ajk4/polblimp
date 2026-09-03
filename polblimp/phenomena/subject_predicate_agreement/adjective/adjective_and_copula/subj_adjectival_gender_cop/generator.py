from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms


def run_subj_adjectival_gender_cop(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(_sentence: conllu.TokenList, match: Match) -> bool:
        root_feats = match["root"]["feats"] or {}
        cop_feats = match["cop"]["feats"] or {}
        if root_feats.get("Gender") is None or cop_feats.get("Gender") is None:
            return False
        if root_feats.get("Number") == "Sing" and root_feats.get("Gender") != cop_feats.get("Gender"):
            return False

        target_gender = get_target_gender(match["root"])
        if target_gender is None:
            return False

        return (
            change_gender(match["root"], morph_dict, target_gender=target_gender)
            and change_gender(match["cop"], morph_dict, target_gender=target_gender)
        )

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (QueryVariant("1a", ("root", "cop"), transform, "subj_adjectival_gender_cop"),),
        limit,
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
