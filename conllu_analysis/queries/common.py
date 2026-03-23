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
        match_token_fn: Callable[[conllu.TokenList], Optional[conllu.Token]],
        transform_inplace_fn: Callable[[conllu.Token], Optional[conllu.Token]],
        limit: Optional[int] = None,
        progress_desc: Optional[str] = None,
) -> pd.DataFrame:
    rows: list[tuple[int, str, str]] = []
    matched_sentences = 0

    iterator = tqdm(
        enumerate(sentences),
        total=len(sentences),
        desc=progress_desc or "processing",
    )

    for index, sentence in iterator:
        if limit is not None and len(rows) >= limit:
            break

        sentence_copy = deepcopy(sentence)
        token = match_token_fn(sentence_copy)
        if token is None:
            continue
        matched_sentences += 1

        modified_token = transform_inplace_fn(token)
        if modified_token is None:
            continue

        correct_text = sentence.metadata.get("text") or sentence_text(sentence)
        incorrect_text = sentence_text(sentence_copy)
        rows.append((index, correct_text, incorrect_text))

    df = pd.DataFrame(rows, columns=["conllu_index", "correct", "incorrect"])
    df.attrs["matched_sentences"] = matched_sentences
    return df


def change_number(token: conllu.Token, morph_dict: MorphDictionary) -> Optional[conllu.Token]:
    source_xpos = token["xpos"]
    if "pl" in source_xpos:
        target_xpos = source_xpos.replace("pl", "sg")
    elif "sg" in source_xpos:
        target_xpos = source_xpos.replace("sg", "pl")
    else:
        print("Unknown tag", source_xpos)
        return None

    return change_morph(token, morph_dict, target_xpos)


def change_person(token: conllu.Token, morph_dict: MorphDictionary) -> Optional[conllu.Token]:
    source_xpos = token["xpos"]
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
        return None

    return change_morph(token, morph_dict, target_xpos)


def change_gender(
        token: conllu.Token,
        morph_dict: MorphDictionary,
) -> Optional[conllu.Token]:
    source_xpos = token["xpos"]

    if ":n:" in source_xpos:
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
        return None

    return change_morph(token, morph_dict, target_xpos)


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
) -> Optional[conllu.Token]:
    lemma = token.get("lemma")
    if not lemma or not morph_dict.has_lemma(lemma):
        print("Missing lemma", lemma)
        return None

    target_form = morph_dict.get_form(lemma, target_tag)
    if target_form is None:
        print(f"Missing form, lemma: {lemma}, form: {target_tag}")
        return None

    form = token.get("form", "")
    if form and form[0].isupper():
        target_form = target_form[:1].upper() + target_form[1:]

    token["form"] = target_form
    token["xpos"] = target_tag
    return token
