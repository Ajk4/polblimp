from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from ..common import change_morph, match_descendants, run_filter_transform, change_person_root, change_person
from ..morph_dictionary import MorphDictionary


def run_subj_pred_person_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_person_simple(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        return change_person(matches['cop'], morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_pred_person_simple,
        transform,
        limit=limit,
        progress_desc="subj_pred_person_simple",
    )


def match_subj_pred_person_simple(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_pred_person_simple(sentence) is not None

def extract_subj_pred_person_simple(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    if root.token["upos"] == "VERB":
        return None
    if root.token["deprel"] != "root":
        return None

    nsubj = None
    for child in root.children:
        if child.token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue

        descendants = match_descendants(
            child,
            lambda token: token["deprel"] in {"nmod", "nmod:poss", "xcomp", "conj", "nummod"},
        )
        if descendants:
            continue

        nsubj = child
        break

    if nsubj is None:
        return None

    cop = None
    for child in root.children:
        if child.token["upos"] != "AUX":
            continue
        if child.token.get("lemma") in {"to", "by"}:
            continue
        if cop is None:
            cop = child

    if cop is None:
        return None

    return {
        "root": root.token,
        "nsubj": nsubj.token,
        "cop": cop.token,
    }
