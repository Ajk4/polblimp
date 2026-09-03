from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms


def run_subj_adjectival_gender(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_gender(match["root"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (QueryVariant("1a", ("root",), transform, "subj_adjectival_gender"),),
        limit,
    )


def match_subj_adjectival_gender(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["upos"] != "ADJ":
        return []
    if root_token["deprel"] != "root":
        return []

    nsubjs = [
        child.token
        for child in root.children
        if child.token["deprel"] in {"nsubj", "nsubj:pass"}
        and (child.token["feats"] or {}).get("Case") == "Nom"
        and (child.token["feats"] or {}).get("Person") not in {"1", "2"}
    ]
    cops = [
        child.token
        for child in root.children
        if child.token["upos"] == "AUX" and child.token.get("lemma") not in {"to", "by"}
    ]
    return [
        {
            "root": root_token,
            "nsubj": nsubj_token,
            "cop": cop_token,
        }
        for nsubj_token in nsubjs
        for cop_token in cops
    ]
