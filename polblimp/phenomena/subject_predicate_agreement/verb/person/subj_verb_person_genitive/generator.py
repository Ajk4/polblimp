from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import QUANTIFIER_LEMMAS, append_aux_clitic, change_person, run_filter_transform, token_trees
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_person_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_person_genitive_1a(sentence)
        return change_person(matches[0]["root"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_genitive_1a(s)) != 0,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_person_genitive__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_person_genitive_1b(sentence)
        return append_aux_clitic(matches[0]["root"], morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_genitive_1b(s)) != 0,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_person_genitive__1b",
    )

    variants = [variant_1a, variant_1b]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


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
