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
    def transform(sentence: conllu.TokenList) -> bool:
        matches = match_subj_adjectival_gender_cop(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"

        target_gender = get_target_gender(matches["root"])
        if target_gender is None:
            return False

        root_form = matches["root"]["form"]
        cop_form = matches["cop"]["form"]
        changed = (
            change_gender(matches["root"], morph_dict, target_gender=target_gender)
            and change_gender(matches["cop"], morph_dict, target_gender=target_gender)
        )
        return changed and (
            matches["root"]["form"] != root_form
            or matches["cop"]["form"] != cop_form
        )

    return run_filter_transform(
        sentences,
        lambda s: match_subj_adjectival_gender_cop(s) is not None,
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
    gender = (token["feats"] or {}).get("Gender")
    if gender == "Masc":
        return "Fem"
    if gender in {"Fem", "Neut"}:
        return "Masc"
    return None
