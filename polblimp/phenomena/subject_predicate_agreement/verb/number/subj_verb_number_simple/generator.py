from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import run_filter_transform, change_number_root, match_descendants
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_number_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_simple,
        lambda sentence: change_number_root(sentence, morph_dict),
        limit=limit,
        progress_desc=f"run_subj_verb_number_simple",
    )


def match_subj_verb_number_simple(
        sentence: conllu.TokenList,
) -> bool:
    root = sentence.to_tree()
    if root.token["upos"] != "VERB":
        return False

    root_feats = root.token['feats']
    if 'Number' not in root_feats:
        return False

    for child in root.children:
        child_token = child.token

        if child_token["upos"] != "NOUN":
            continue

        if child_token["deprel"] != "nsubj":
            continue

        child_feats = child_token['feats']
        if child_feats.get('Number', "") != root_feats['Number']:
            continue

        def descendant_predicate(token: conllu.Token) -> bool:
            feats = token['feats']
            if feats is None:
                return False

            return (token['deprel'] in {"nmod", "nmod:poss", "xcomp", "conj", "nummod"})

        unwanted_descendants = match_descendants(child, descendant_predicate)
        if len(unwanted_descendants) == 0:
            return True

    return False
