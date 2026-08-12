from __future__ import annotations

import random
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import preserve_case, remove_token_preserving_spacing, run_filter_transform, token_trees
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.common import (
    append_aux_clitic,
    change_aux_clitic_person,
    change_person,
)

def run_subj_verb_person_simple(sentences: list[conllu.TokenList], morph_dict: MorphDictionary,
                                limit: Optional[int]) -> pd.DataFrame:
    # Main verb
    def transform_1a(sentence) -> bool:
        matches = match_subj_verb_person_simple_1a(sentence)
        return change_person(matches[0]["root_tree"], morph_dict)

    variant_1a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_1a(s)) != 0,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_person__1a",
    )

    def transform_1b(sentence) -> bool:
        match = match_subj_verb_person_simple_1b(sentence)[0]
        source_person = (match["nsubj"]["feats"] or {})["Person"]
        return change_or_remove_aux_clitic(sentence, match["auxclitic"], source_person, morph_dict)

    variant_1b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_1b(s)) != 0,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_person__1b",
    )

    def transform_1c(sentence) -> bool:
        match = match_subj_verb_person_simple_1c(sentence)[0]
        if "auxcnd" in match:
            return change_conditional_person(match["root"], match["auxcnd"], morph_dict)
        if match["root"]["lemma"] == "powinien":
            return append_aux_clitic(match["root"], morph_dict)
        return change_person(match["root_tree"], morph_dict)

    variant_1c = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_1c(s)) != 0,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_person__1c",
    )

    def transform_1d(sentence) -> bool:
        matches = match_subj_verb_person_simple_1d(sentence)[0]
        if "auxcnd" in matches:
            # Conditional is split in UD as past host + "by" (e.g. "był" + "by").
            # Person attaches to the conditional particle ("byś"), not the host
            # ("byłeśby" is invalid).
            return change_conditional_person(matches["aux"], matches["auxcnd"], morph_dict)
        return change_person(matches['aux_tree'], morph_dict)

    variant_1d = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_1d(s)) != 0,
        transform_1d,
        limit=limit,
        progress_desc="subj_verb_person__1d",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_person_simple_2a(sentence)
        return change_person(matches[0]['cop_tree'], morph_dict)
    variant_2a = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_2a(s)) != 0,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_person__2a",
    )

    def transform_2b(sentence) -> bool:
        match = match_subj_verb_person_simple_2b(sentence)[0]
        source_person = (match["nsubj"]["feats"] or {})["Person"]
        return change_or_remove_aux_clitic(sentence, match["auxclitic"], source_person, morph_dict)

    variant_2b = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_2b(s)) != 0,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_person__2b",
    )

    def transform_2c(sentence) -> bool:
        matches = match_subj_verb_person_simple_2c(sentence)[0]
        if "auxcnd" in matches:
            # Conditional is split in UD as past host + "by" (e.g. "był" + "by").
            # Person attaches to the conditional particle ("byś"), not the host
            # ("byłeśby" is invalid).
            return change_conditional_person(matches["cop"], matches["auxcnd"], morph_dict)
        return change_person(matches['cop_tree'], morph_dict)

    variant_2c = run_filter_transform(
        sentences,
        lambda s: len(match_subj_verb_person_simple_2c(s)) != 0,
        transform_2c,
        limit=limit,
        progress_desc="subj_verb_person__2c",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_1d, variant_2a, variant_2b, variant_2c]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df

def change_or_remove_aux_clitic(
        sentence: conllu.TokenList,
        auxclitic: Token,
        source_person: str,
        morph_dict: MorphDictionary,
) -> bool:
    if random.randint(0, 1) == 0:
        return change_aux_clitic_person(auxclitic, source_person, morph_dict)
    return remove_token_preserving_spacing(sentence, auxclitic)


def change_conditional_person(aux: Token, auxcnd: Token, morph_dict: MorphDictionary) -> bool:
    aux_xpos = aux["xpos"]
    if ":pl:" in aux_xpos:
        target_number = "pl"
    elif ":sg:" in aux_xpos:
        target_number = "sg"
    else:
        print(f"Unknown conditional aux number, tag={aux_xpos}, form={aux['form']}")
        return False

    target_person = "pri" if random.randint(0, 1) == 0 else "sec"
    by_form = auxcnd["form"]

    clitic_xpos = f"aglt:{target_number}:{target_person}:imperf:nwok"
    clitic_form = morph_dict.get_form("być", clitic_xpos)
    if clitic_form is None:
        print(f"Missing form, lemma: być, target_tag: {clitic_xpos}")
        return False

    auxcnd["form"] = preserve_case(by_form, by_form + clitic_form)
    return True


def match_subj_verb_person_simple_1a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}
        if root_token["upos"] != "VERB":
            continue
        if root_feats.get("Tense") not in {"Pres", "Fut"}:
            continue
        if root_feats.get("Person") not in {"1", "2", "3"}:
            continue
        matches.extend(extract_main_verb_person_subject_matches(root))

    return matches


def match_subj_verb_person_simple_1b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}
        auxclitic = extract_child(root, "aux:clitic")
        if root_token["upos"] != "VERB":
            continue
        if root_feats.get("Tense") != "Past" and root_token["lemma"] != "powinien":
            continue
        if auxclitic is None:
            continue

        for match in extract_main_verb_person_subject_matches(root):
            if (match["nsubj"]["feats"] or {}).get("Person") not in {"1", "2"}:
                continue
            matches.append({
                **match,
                "auxclitic": auxclitic.token,
            })

    return matches


def match_subj_verb_person_simple_1c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        root_feats = root_token["feats"] or {}
        if root_token["upos"] != "VERB":
            continue
        if root_feats.get("Tense") != "Past" and root_token["lemma"] != "powinien":
            continue
        if extract_child(root, "aux") is not None:
            continue

        auxcnd = extract_child(root, "aux:cnd")
        for match in extract_main_verb_person_subject_matches(root):
            if (match["nsubj"]["feats"] or {}).get("Person") in {"1", "2"}:
                continue
            if auxcnd is not None:
                match["auxcnd"] = auxcnd.token
            matches.append(match)

    return matches


def match_subj_verb_person_simple_1d(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        root_token = root.token
        if root_token["upos"] != "VERB":
            continue
        if root_token["lemma"] == "to":
            continue

        aux = extract_child(root, "aux")
        if aux is None:
            continue
        auxcnd = extract_child(root, "aux:cnd")

        for match in extract_main_verb_person_subject_matches(root):
            result = {
                **match,
                "aux": aux.token,
                "aux_tree": aux,
            }
            if auxcnd is not None:
                result["auxcnd"] = auxcnd.token
            matches.append(result)

    return matches


def match_subj_verb_person_simple_2a(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return [
        match
        for match in extract_copular_person_matches(sentence)
        if (match["cop"]["feats"] or {}).get("Tense") in {"Pres", "Fut"}
    ]


def match_subj_verb_person_simple_2b(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        auxclitic = extract_child(root, "aux:clitic")
        if auxclitic is None:
            continue

        for match in extract_copular_person_matches_for_root(root):
            cop_feats = match["cop"]["feats"] or {}
            nsubj_feats = match["nsubj"]["feats"] or {}
            if cop_feats.get("Tense") != "Past":
                continue
            if nsubj_feats.get("Person") not in {"1", "2"}:
                continue
            matches.append({
                **match,
                "auxclitic": auxclitic.token,
            })

    return matches


def match_subj_verb_person_simple_2c(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        auxcnd = extract_child(root, "aux:cnd")
        for match in extract_copular_person_matches_for_root(root):
            cop_feats = match["cop"]["feats"] or {}
            nsubj_feats = match["nsubj"]["feats"] or {}
            if cop_feats.get("Tense") != "Past":
                continue
            if nsubj_feats.get("Person") in {"1", "2"}:
                continue
            result = dict(match)
            if auxcnd is not None:
                result["auxcnd"] = auxcnd.token
            matches.append(result)

    return matches


def extract_main_verb_person_subject_matches(root: conllu.TokenTree) -> list[dict[str, Token]]:
    matches = []
    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue
        matches.append({
            "root": root.token,
            "root_tree": root,
            "nsubj": nsubj_token,
        })

    return matches


def extract_copular_person_matches(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    matches = []
    for root in token_trees(sentence.to_tree()):
        matches.extend(extract_copular_person_matches_for_root(root))

    return matches


def extract_copular_person_matches_for_root(root: conllu.TokenTree) -> list[dict[str, Token]]:
    root_token = root.token
    matches = []
    if root_token["upos"] == "VERB" and root_token.get("lemma") != "to":
        return matches

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue

        for cop in root.children:
            cop_token = cop.token
            if cop_token["upos"] != "AUX":
                continue
            if cop_token.get("lemma") in {"to", "by"}:
                continue
            matches.append({
                "root": root_token,
                "nsubj": nsubj_token,
                "cop": cop_token,
                "cop_tree": cop,
            })

    return matches


def extract_child(root: conllu.TokenTree, deprel: str) -> conllu.TokenTree | None:
    for child in root.children:
        if child.token["deprel"] == deprel:
            return child

    return None
