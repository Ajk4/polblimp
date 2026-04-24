
from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import match_descendants, run_filter_transform, change_gender_root, change_gender
from .morph_dictionary import MorphDictionary

"""
Query for ADJ:
a-node $root := [
  tag = 'ADJ',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    member iset [gender = $root.iset/gender],
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],
  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]

Query for the rest (so we don’t exclude present and future from adjectival):

a-node $root := [
  tag != 'VERB',
  tag != 'ADJ',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',
    0x descendant [deprel = 'nmod' or deprel = 'nmod:poss'or deprel = 'xcomp' or deprel = 'conj' or deprel = 'nummod'],
    ],
  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
    member iset [tense = 'past']
  ]
]


"""


def run_subj_pred_gender_simple(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_adj(sentence: conllu.TokenList):
        matches = extract_subj_pred_gender_simple__adj(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"
        cop = matches['cop']
        if cop['feats']['Tense'] == "Past":
            return change_gender(matches['root'], morph_dict) and change_gender(cop, morph_dict)
        else:
            return change_gender(matches['root'], morph_dict)

    variant_adj = run_filter_transform(
        sentences,
        match_subj_pred_gender_simple__adj,
        transform_adj,
        limit=limit,
        progress_desc="subj_pred_gender_simple__adj",
    )

    def transform_other(sentence: conllu.TokenList):
        matches = extract_subj_pred_gender_simple__other(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"
        return change_gender(matches['cop'], morph_dict)
    variant_other = run_filter_transform(
        sentences,
        match_subj_pred_gender_simple__other,
        transform_other,
        limit=limit,
        progress_desc="subj_pred_gender_simple__other",
    )

    df = pd.concat([variant_adj, variant_other])
    df.attrs["matched_sentences"] = (
        variant_adj.attrs.get("matched_sentences", 0) +
        variant_other.attrs.get("matched_sentences", 0)
    )
    return df


def match_subj_pred_gender_simple__adj(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_pred_gender_simple__adj(sentence) is not None


def match_subj_pred_gender_simple__other(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_pred_gender_simple__other(sentence) is not None


def extract_subj_pred_gender_simple__adj(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}
    root_gender = root_feats.get("Gender")

    if root.token["deprel"] != "root":
        return None

    if root.token["upos"] != "ADJ":
        return None

    nsubj = None
    for child in root.children:
        child_feats = child.token["feats"] or {}
        if child.token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue

        descendants = match_descendants(
            child,
            lambda token: token["deprel"] in {"nmod", "nmod:poss", "xcomp", "conj", "nummod"},
        )
        if descendants:
            continue

        if child_feats.get("Gender") != root_gender:
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
        cop = child
        break

    if cop is None:
        return None

    return {
        "root": root.token,
        "nsubj": nsubj.token,
        "cop": cop.token,
    }


def extract_subj_pred_gender_simple__other(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()

    if root.token["deprel"] != "root":
        return None
    if root.token["upos"] in {"VERB", "ADJ"}:
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
        child_feats = child.token["feats"] or {}
        if child.token["upos"] != "AUX":
            continue
        if child.token.get("lemma") in {"to", "by"}:
            continue
        if child_feats.get("Tense") != "Past":
            continue
        cop = child
        break

    if cop is None:
        return None

    return {
        "root": root.token,
        "nsubj": nsubj.token,
        "cop": cop.token,
    }
