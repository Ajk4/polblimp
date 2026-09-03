from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import (
    QUANTIFIER_LEMMAS,
    token_trees,
)
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.verb.person.common import (
    append_aux_clitic,
    change_person,
)


def run_subj_verb_person_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform_1a(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_person(match["root_tree"], morph_dict)

    def transform_1b(_sentence: conllu.TokenList, match: Match) -> bool:
        return append_aux_clitic(match["root"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (
            QueryVariant("1a", ("root",), transform_1a, "subj_verb_person_genitive__1a"),
            QueryVariant("1b", ("root",), transform_1b, "subj_verb_person_genitive__1b"),
        ),
        limit,
    )


def match_subj_verb_person_genitive_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if root_feats.get("Tense") not in {"Pres", "Fut"}:
            continue
        if root_feats.get("Person") != "3":
            continue
        matches.extend(extract_genitive_subject_matches(root))

    return matches


def match_subj_verb_person_genitive_1b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}

        if root_token["upos"] != "VERB":
            continue
        if not (root_feats.get("Tense") == "Past" or root_token["lemma"] == "powinien"):
            continue
        matches.extend(extract_genitive_subject_matches(root))

    return matches


def extract_genitive_subject_matches(root: conllu.TokenTree) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}

        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Case") != "Gen":
            continue
        if has_numeral_or_quantifier_child(nsubj):
            continue

        matches.append({
            "root": root_token,
            "root_tree": root,
            "nsubj": nsubj_token,
        })

    return matches


def has_numeral_or_quantifier_child(nsubj: conllu.TokenTree) -> bool:
    for child in nsubj.children:
        child_token = child.token
        if child_token["upos"] == "NUM":
            return True
        if child_token["deprel"].startswith("det") and child_token["lemma"] in QUANTIFIER_LEMMAS:
            return True

    return False
