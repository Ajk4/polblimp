from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_number, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_adjectival_number_cop(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = match_subj_adjectival_number_cop(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"
        return (
            change_number(matches["root"], morph_dict)
            and change_number(matches["cop"], morph_dict)
        )

    return run_filter_transform(
        sentences,
        lambda s: match_subj_adjectival_number_cop(s) is not None,
        transform,
        limit=limit,
        progress_desc="subj_adjectival_number_cop",
    )


def match_subj_adjectival_number_cop(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["upos"] != "ADJ":
        return None
    if root_token["deprel"] != "root":
        return None

    nsubj_token = None
    for child in root.children:
        child_token = child.token
        if child_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        nsubj_token = child_token
        break

    if nsubj_token is None:
        return None

    for child in root.children:
        child_token = child.token
        if child_token["upos"] != "AUX":
            continue
        if child_token.get("lemma") in {"to", "by"}:
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
            "cop": child_token,
        }

    return None
