from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import match_descendants, run_filter_transform, change_number
from .morph_dictionary import MorphDictionary


def match_subj_verb_number_pp_attractor(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()

    if root.token["upos"] != "VERB":
        return None

    root_number = root.token["feats"].get("Number")

    for nsubj in root.children:
        if nsubj.token["upos"] != "NOUN":
            continue
        if nsubj.token["deprel"] != "nsubj":
            continue

        nsubj_feats = nsubj.token["feats"]
        if nsubj_feats.get("Number", "") != root_number:
            continue

        def match_attractor(token: conllu.Token) -> bool:
            return token['deprel'] in {'nmod', "nmod:poss", "xcomp", "conj"}

        attractors = match_descendants(nsubj, match_attractor)
        if len(attractors) != 1:
            continue

        for attractor in nsubj.children:
            if attractor.token["upos"] != "NOUN":
                continue
            if attractor.token["deprel"] != "nmod":
                continue

            attractor_feats = attractor.token["feats"]
            if attractor_feats.get("Number", "") == root_number:
                continue

            for prep in attractor.children:
                if prep.token["upos"] != "ADP":
                    continue
                if prep.token["deprel"] != "case":
                    continue

                if prep.token['lemma'] == 'z' and attractor_feats.get("Case") != "Ins":
                    return root.token
                if prep.token['lemma'] != 'z':
                    return root.token

    return None


def run_subj_verb_number_pp_attractor(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    return run_filter_transform(
        sentences,
        match_subj_verb_number_pp_attractor,
        lambda token: change_number(token, morph_dict),
        limit=limit,
        progress_desc="subj_verb_number_pp_attractor",
    )
