from __future__ import annotations

import random
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import run_filter_transform, change_person_root, match_children, change_person
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

    # TODO simplify remove_aux_clitic
    variant_1b = run_filter_transform(
        sentences,
        match_subj_verb_person_1b,
        remove_aux_clitic,
        limit=limit,
        progress_desc="subj_verb_person__1b",
    )

    variant_1c = run_filter_transform(
        sentences,
        match_subj_verb_person_1c,
        append_aux_clitic,
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

    )

    variants = [variant_1a, variant_1b, variant_1c, variant_1d]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(len(df) for df in variants)

    return df


def append_aux_clitic(sentence: conllu.TokenList) -> bool:
    root = sentence.to_tree().token
    root_form = root["form"]
    if random.randint(0, 1) == 0:
        root["form"] = root_form + "em"
    else:
        root["form"] = root_form + "eś"
    return True


def remove_aux_clitic(sentence: conllu.TokenList) -> bool:
    root = sentence.to_tree().token
    root_id = root["id"]
    clitic_indexes = [
        index
        for index, token in enumerate(sentence)
        if token.get("head") == root_id and token.get("deprel") == "aux:clitic"
    ]
    if not clitic_indexes:
        return False

    clitic_misc = sentence[clitic_indexes[-1]].get("misc") or {}
    root_misc = {
        key: value
        for key, value in (root.get("misc") or {}).items()
        if key != "SpaceAfter"
    }
    root_misc.update({
        key: value
        for key, value in clitic_misc.items()
        if key == "SpaceAfter"
    })
    root["misc"] = root_misc or None

    for index in reversed(clitic_indexes):
        del sentence[index]

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


def match_subj_verb_person_1b(sentence: conllu.TokenList) -> bool:
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

        if not (root_feats.get("Tense") == "Past" or root.token["lemma"] == "powinien"):
            continue

        if not (nsubj_feats.get("Person", "") in {"1", "2"}):
            continue

        for auxclitic in root.children:
            if auxclitic.token["deprel"] == "aux:clitic":
                return True

    return False


def match_subj_verb_person_1c(sentence: conllu.TokenList) -> bool:
    root = sentence.to_tree()

    if not (root.token["upos"] == "VERB"):
        return False

    if not (root.token["deprel"] == "root"):
        return False

    root_feats = root.token["feats"]

    if not (root_feats.get("Tense", "") == "Past" or root.token['lemma'] == 'powinien'):
        return False

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

        return True

    return False


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
