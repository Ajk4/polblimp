from __future__ import annotations

import random
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional

import conllu
import pandas as pd
from tqdm import tqdm

from .morph_dictionary import MorphDictionary


def run_filter_transform(
        sentences: list[conllu.TokenList],
        match_sentence_fn: Callable[[conllu.TokenList], bool],
        transform_inplace_fn: Callable[[conllu.TokenList], bool],
        limit: Optional[int] = None,
        progress_desc: Optional[str] = None,
) -> pd.DataFrame:
    rows: list[tuple[str, int, str, str]] = []
    matched_sentences = 0

    iterator = tqdm(
        enumerate(sentences),
        total=len(sentences),
        desc=progress_desc or "processing",
    )

    for index, sentence in iterator:
        if limit is not None and len(rows) >= limit:
            break

        metadata = sentence.metadata or {}
        sentence_copy = deepcopy(sentence)
        if not match_sentence_fn(sentence_copy):
            continue
        matched_sentences += 1

        if not transform_inplace_fn(sentence_copy):
            continue

        correct_text = metadata.get("text") or sentence_text(sentence)
        incorrect_text = sentence_text(sentence_copy)
        dataset = metadata.get("dataset", "")
        rows.append((dataset, index, correct_text, incorrect_text))

    df = pd.DataFrame(rows, columns=["dataset", "conllu_index", "correct", "incorrect"])
    df.attrs["matched_sentences"] = matched_sentences
    return df


def change_number(sentence: conllu.TokenList, morph_dict: MorphDictionary) -> bool:
    root = sentence.to_tree().token
    source_xpos = root["xpos"]
    if "pl" in source_xpos:
        target_xpos = source_xpos.replace("pl", "sg")
    elif "sg" in source_xpos:
        target_xpos = source_xpos.replace("sg", "pl")
    else:
        print("Unknown tag", source_xpos)
        return False

    return change_morph(sentence.to_tree().token, morph_dict, target_xpos)


def change_person(sentence: conllu.TokenList, morph_dict: MorphDictionary) -> bool:
    root = sentence.to_tree().token
    source_xpos = root["xpos"]
    if ":pri:" in source_xpos:
        if random.randint(0, 1) == 0:
            target_xpos = source_xpos.replace(":pri:", ":sec:")
        else:
            target_xpos = source_xpos.replace(":pri:", ":ter:")
    elif ":sec:" in source_xpos:
        if random.randint(0, 1) == 0:
            target_xpos = source_xpos.replace(":sec:", ":pri:")
        else:
            target_xpos = source_xpos.replace(":sec:", ":ter:")
    elif ":ter:" in source_xpos:
        if random.randint(0, 1) == 0:
            target_xpos = source_xpos.replace(":ter:", ":pri:")
        else:
            target_xpos = source_xpos.replace(":ter:", ":sec:")
    else:
        print("Unknown tag", source_xpos)
        return False

    return change_morph(sentence.to_tree().token, morph_dict, target_xpos)


def change_gender(
        sentence: conllu.TokenList,
        morph_dict: MorphDictionary,
) -> bool:
    root = sentence.to_tree().token
    source_xpos = root["xpos"]

    if source_xpos in {'praet:sg:m1:imperf', 'praet:sg:m2:imperf', 'praet:sg:m3:imperf'}:
        # In this case all m1.m2.m3 are the same, so replace with n1.n2
        target_xpos = 'praet:sg:n1.n2:imperf'
    elif ":n:" in source_xpos:
        if random.randint(0, 1) == 0:
            target_xpos = source_xpos.replace(":n:", ":m1:")
        else:
            target_xpos = source_xpos.replace(":n:", ":f:")
    elif ":f" in source_xpos:
        target_xpos = source_xpos.replace(":f:", ":m1:")
    elif ":m1" in source_xpos:
        target_xpos = source_xpos.replace(":m1:", ":f:")
    elif ":m2" in source_xpos:
        target_xpos = source_xpos.replace(":m2:", ":m1:")
    elif ":m3" in source_xpos:
        target_xpos = source_xpos.replace(":m3:", ":m1:")
    else:
        print("Unknown tag", source_xpos)
        return False

    return change_morph(sentence.to_tree().token, morph_dict, target_xpos)


def match_descendants(tree: conllu.TokenTree, token_predicate):
    matches = []
    for child in tree.children:
        if token_predicate(child.token):
            matches.append(child.token)
        matches.extend(match_descendants(child, token_predicate))
    return matches


def load_sentences(conllu_path: Path, limit=None) -> list[conllu.TokenList]:
    sentences: list[conllu.TokenList] = []
    with conllu_path.open("r", encoding="utf-8") as handle:
        for sentence in conllu.parse_incr(handle):
            metadata = sentence.metadata or {}
            metadata["dataset"] = conllu_path.name
            sentence.metadata = metadata
            sentences.append(sentence)
            if limit is not None:
                if len(sentences) >= limit:
                    break
    return sentences


def sentence_text(sentence: conllu.TokenList) -> str:
    out: list[str] = []
    for token in sentence:
        if not isinstance(token["id"], int):
            continue

        out.append(token["form"])
        misc = token.get("misc")
        if not misc or misc.get("SpaceAfter") != "No":
            out.append(" ")

    return "".join(out).rstrip()


def change_morph(
        token: conllu.Token,
        morph_dict: MorphDictionary,
        target_tag: str,
) -> bool:
    lemma = token.get("lemma")
    if not lemma or not morph_dict.has_lemma(lemma):
        print("Missing lemma", lemma)
        return False

    target_form = morph_dict.get_form(lemma, target_tag)
    if target_form is None:
        print(f"Missing form, lemma: {lemma}, form: {target_tag}")
        return False

    form = token.get("form", "")
    if form and form[0].isupper():
        target_form = target_form[:1].upper() + target_form[1:]

    token["form"] = target_form
    token["xpos"] = target_tag
    return True
