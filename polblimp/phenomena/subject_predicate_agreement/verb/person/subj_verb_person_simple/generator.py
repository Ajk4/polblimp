from __future__ import annotations
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import run_filter_transform, change_person_root, match_children, change_person, append_aux_clitic
from phenomena.morph_dictionary import MorphDictionary

def run_subj_verb_person_simple(sentences: list[conllu.TokenList], morph_dict: MorphDictionary,
                                limit: Optional[int]) -> pd.DataFrame:
    # Main verb
    variant_1a = run_filter_transform(
        sentences,
        match_subj_verb_person_1a,
        lambda sentence: change_person_root(sentence, morph_dict),
        limit=limit,
        progress_desc="subj_verb_person__1a",
    )

    def transform_1b(sentence) -> bool:
        matches = match_subj_verb_person_1b(sentence)
        return remove_aux_clitic(sentence, matches["auxclitic"])

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_person__1b",
    )

    def transform_1c(sentence) -> bool:
        matches = match_subj_verb_person_1c(sentence)
        if matches["root"]["lemma"] == "powinien":
            return append_aux_clitic(matches["root"], morph_dict)
        return change_person(matches["root"], morph_dict)

    variant_1c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_1c(s) is not None,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_person__1c",
    )

    def transform_1d(sentence) -> bool:
        matches = extract_subj_verb_person_1d(sentence)
        return change_person(matches['aux'], morph_dict)

    variant_1d = run_filter_transform(
        sentences,
        lambda s: extract_subj_verb_person_1d(s) is not None,
        transform_1d,
        limit=limit,
        progress_desc="subj_verb_person__1d",
    )

    # Copular auxiliary verb
    def transform_2a(sentence) -> bool:
        matches = match_subj_verb_person_2a(sentence)
        return change_person(matches['cop'], morph_dict)
    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_person__2a",
    )

    def transform_2b(sentence) -> bool:
        matches = match_subj_verb_person_2b(sentence)
        return remove_aux_clitic(sentence, matches["auxclitic"])

    variant_2b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_2b(s) is not None,
        transform_2b,
        limit=limit,
        progress_desc="subj_verb_person__2b",
    )

    def transform_2c(sentence) -> bool:
        matches = match_subj_verb_person_2c(sentence)
        return change_person(matches['cop'], morph_dict)

    variant_2c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_person_2c(s) is not None,
        transform_2c,
        limit=limit,
        progress_desc="subj_verb_person__2c",
    )

    variants = [variant_1a, variant_1b, variant_1c, variant_1d, variant_2a, variant_2b, variant_2c]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df

def remove_aux_clitic(sentence: conllu.TokenList, auxclitic: Token) -> bool:
    clitic_index = None
    for index, token in enumerate(sentence):
        if token is auxclitic:
            clitic_index = index
            break

    if clitic_index is None:
        return False

    clitic_misc = auxclitic.get("misc") or {}

    previous_token = None
    for token in reversed(sentence[:clitic_index]):
        if isinstance(token["id"], int):
            previous_token = token
            break

    if previous_token is not None:
        previous_misc = {
            key: value
            for key, value in (previous_token.get("misc") or {}).items()
            if key != "SpaceAfter"
        }
        if clitic_misc.get("SpaceAfter") == "No":
            previous_misc["SpaceAfter"] = "No"
        previous_token["misc"] = previous_misc or None

    del sentence[clitic_index]

    return True


def match_subj_verb_person_1a(sentence: conllu.TokenList) -> bool:
    root = sentence.to_tree()

    if not (root.token["upos"] == "VERB"):
        return False

    if not (root.token["deprel"] == "root"):
        return False

    root_feats = root.token["feats"]

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"]

        if not (nsubj_token["deprel"] == "nsubj"):
            continue

        if not (nsubj_feats.get("Case") != "Gen"):
            continue

        if root_feats.get("Tense", "") in {"Pres", "Fut"} and root_feats.get("Person", "") in {"1", "2", "3"}:
            return True

    return False


def match_subj_verb_person_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()

    if not (root.token["upos"] == "VERB"):
        return None

    if not (root.token["deprel"] == "root"):
        return None

    root_feats = root.token["feats"]

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"]

        if not (nsubj_token["deprel"] == "nsubj"):
            continue

        if not (nsubj_feats.get("Case") != "Gen"):
            continue

        if not (root_feats.get("Tense") == "Past" or root.token["lemma"] == "powinien"):
            continue

        if not (nsubj_feats.get("Person", "") in {"1", "2"}):
            continue

        for auxclitic in root.children:
            if auxclitic.token["deprel"] == "aux:clitic":
                return {
                    "root": root.token,
                    "nsubj": nsubj_token,
                    "auxclitic": auxclitic.token,
                }

    return None


def match_subj_verb_person_1c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()

    if not (root.token["upos"] == "VERB"):
        return None

    if not (root.token["deprel"] == "root"):
        return None

    root_feats = root.token["feats"]

    if not (root_feats.get("Tense", "") == "Past" or root.token['lemma'] == 'powinien'):
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"]

        if not (nsubj_token["deprel"] == "nsubj"):
            continue

        if not (nsubj_feats.get("Case") != "Gen"):
            continue

        if not (nsubj_feats.get("Person", "") not in {"1", "2"}):
            continue

        if not (len(match_children(root, lambda ch: ch["deprel"] == "aux")) == 0):
            continue

        return {
            "root": root.token,
            "nsubj": nsubj_token,
        }

    return None


def extract_subj_verb_person_1d(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()

    if not (root.token["upos"] == "VERB"):
        return None

    if not (root.token["deprel"] == "root"):
        return None

    if not (root.token['lemma'] != 'to'):
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"]

        if not (nsubj_token["deprel"] == "nsubj"):
            continue

        if not (nsubj_feats.get("Case") != "Gen"):
            continue

        for aux in root.children:
            if aux.token["deprel"] == "aux":
                return {
                    "root": root.token,
                    "aux": aux.token,
                }

    return None


def match_subj_verb_person_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token.get("lemma") != "to":
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue

        for cop in root.children:
            cop_token = cop.token
            cop_feats = cop_token["feats"] or {}
            if cop_token["upos"] != "AUX":
                continue
            if cop_token.get("lemma") in {"to", "by"}:
                continue
            if cop_feats.get("Tense") in {"Pres", "Fut"}:
                return {
                    "root": root_token,
                    "nsubj": nsubj_token,
                    "cop": cop_token,
                }

    return None

def match_subj_verb_person_2b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token.get("lemma") != "to":
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue
        if nsubj_feats.get("Person") not in {"1", "2"}:
            continue

        cop = None
        for child in root.children:
            child_token = child.token
            child_feats = child_token["feats"] or {}
            if child_token["upos"] != "AUX":
                continue
            if child_token.get("lemma") in {"to", "by"}:
                continue
            if child_feats.get("Tense") != "Past":
                continue
            cop = child
            break

        if cop is None:
            continue

        for child in root.children:
            if child.token["deprel"] == "aux:clitic":
                return {
                    "root": root_token,
                    "nsubj": nsubj_token,
                    "cop": cop.token,
                    "auxclitic": child.token,
                }

    return None

def match_subj_verb_person_2c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token.get("lemma") != "to":
        return None

    cop = None
    for child in root.children:
        child_token = child.token
        child_feats = child_token["feats"] or {}
        if child_token["upos"] != "AUX":
            continue
        if child_token.get("lemma") in {"to", "by"}:
            continue
        if child_feats.get("Tense") != "Past":
            continue
        cop = child
        break

    if cop is None:
        return None

    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
            continue
        if nsubj_feats.get("Case") == "Gen":
            continue
        if nsubj_feats.get("Person") in {"1", "2"}:
            continue
        return {
            "root": root_token,
            "nsubj": nsubj_token,
            "cop": cop.token,
        }

    return None
