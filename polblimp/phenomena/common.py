from __future__ import annotations

import random
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional

import conllu
import pandas as pd
from babel.localtime import _win32
from conllu import Token, TokenList
from torch import _C
from torch.onnx._internal.fx import _pass
from tqdm import tqdm

from phenomena.morph_dictionary import MorphDictionary


def run_filter_transform(
        sentences: list[conllu.TokenList],
        match_sentence_fn: Callable[[conllu.TokenList], bool],
        transform_inplace_fn: Callable[[conllu.TokenList], bool],
        limit: Optional[int] = None,
        progress_desc: Optional[str] = None,
) -> pd.DataFrame:
    rows: list[tuple[str, int, str, str]] = []
    matched_sentences = 0
    seed_namespace = progress_desc or "processing"

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

        random.seed(f"{seed_namespace}:{metadata.get('text') or sentence_text(sentence)}")
        if not transform_inplace_fn(sentence_copy):
            continue

        correct_text = metadata.get("text") or sentence_text(sentence)
        incorrect_text = sentence_text(sentence_copy)

        assert correct_text != incorrect_text

        dataset = metadata.get("dataset", "")
        rows.append((dataset, index, correct_text, incorrect_text))

    df = pd.DataFrame(rows, columns=["dataset", "conllu_index", "correct", "incorrect"])
    df.attrs["matched_sentences"] = matched_sentences
    return df


def change_aux_clitic_number(host: Token, token: Token, morph_dict: MorphDictionary) -> bool:
    feats = token["feats"] or {}
    target_number = {"Sing": "pl", "Plur": "sg"}.get(feats.get("Number"))
    target_person = {"1": "pri", "2": "sec"}.get(feats.get("Person"))
    if target_number is None or target_person is None:
        print(f"Unknown aux clitic tag={token['xpos']}, form={token['form']}")
        return False

    target_variant = "nwok"
    if target_number == "sg":
        host_xpos = host["xpos"]
        # Singular aglt has long/short variants: masculine past hosts take vocalic
        # forms (był + em/eś), while feminine/neuter hosts take non-vocalic
        # forms (była/było + m/ś).
        if host_xpos.startswith("praet:sg:m"):
            target_variant = "wok"
        elif not (host_xpos.startswith("praet:sg:f:") or host_xpos.startswith("praet:sg:n")):
            print(f"Unknown host tag for aux clitic, tag={host['xpos']}, form={host['form']}")
            return False

    return change_morph(token, morph_dict, f"aglt:{target_number}:{target_person}:imperf:{target_variant}")


def change_number(token: Token, morph_dict: MorphDictionary) -> bool:
    source_xpos = token["xpos"]
    if "pl" in source_xpos:
        target_xpos = source_xpos.replace("pl", "sg")
    elif "sg" in source_xpos:
        target_xpos = source_xpos.replace("sg", "pl")
        if target_xpos.startswith("praet:pl:") and target_xpos.endswith((":agl", ":nagl")):
            # Remove the final colon-separated :agl/:nagl segment.
            # Plural past forms do not have those variants in the Polimorf dictionary.
            target_xpos = target_xpos.rsplit(":", 1)[0]
    else:
        print("Unknown tag", source_xpos)
        return False

    return change_morph(token, morph_dict, target_xpos)


def change_gender(
        token: Token,
        morph_dict: MorphDictionary,
        target_gender: str | None = None,
) -> bool:
    source_xpos = token["xpos"]
    if target_gender is None:
        target_gender = _select_target_gender(source_xpos)
    if target_gender is None:
        print(f"Unknown tag for gender change, tag={source_xpos}, form={token['form']}")
        return False

    target_xpos = _target_gender_xpos(source_xpos, target_gender)
    if target_xpos is None:
        print(f"Unknown tag for target gender, tag={source_xpos}, form={token['form']}, target_gender={target_gender}")
        return False

    return change_morph(token, morph_dict, target_xpos)


def _select_target_gender(source_xpos: str) -> str | None:
    if source_xpos in {'praet:sg:m1:imperf', 'praet:sg:m2:imperf', 'praet:sg:m3:imperf'}:
        return "Neut"
    if ":n:" in source_xpos:
        return "Masc" if random.randint(0, 1) == 0 else "Fem"
    if ":f" in source_xpos:
        return "Masc"
    if ":m1" in source_xpos:
        return "Fem"
    if ":m2" in source_xpos or ":m3" in source_xpos:
        return "Masc"
    return None


def _target_gender_xpos(source_xpos: str, target_gender: str) -> str | None:
    if target_gender == "Masc":
        if ":sg:" in source_xpos:
            if ":f:" in source_xpos:
                return source_xpos.replace(":f:", ":m1.m2.m3:")
            elif ":n:" in source_xpos:
                return source_xpos.replace(":n:", ":m1.m2.m3:")
            elif ":n1.n2:" in source_xpos:
                return source_xpos.replace(":n1.n2:", ":m1.m2.m3:")
            elif ":m2:" in source_xpos:
                return source_xpos.replace(":m2:", ":m1:")
            elif ":m3:" in source_xpos:
                return source_xpos.replace(":m3:", ":m1:")
        elif ":pl:" in source_xpos:
            if ":m2.m3.f.n1.n2.p2.p3:" in source_xpos:
                return source_xpos.replace(":m2.m3.f.n1.n2.p2.p3:", ":m1.p1:")
            elif ":m2:" in source_xpos:
                return source_xpos.replace(":m2:", ":m1.p1:")
            elif ":m3:" in source_xpos:
                return source_xpos.replace(":m3:", ":m1.p1:")
            elif ":f:" in source_xpos:
                return source_xpos.replace(":f:", ":m1.p1:")
            elif ":n:" in source_xpos:
                return source_xpos.replace(":n:", ":m1.p1:")
            elif ":n1:" in source_xpos:
                return source_xpos.replace(":n1:", ":m1.p1:")
            elif ":n2:" in source_xpos:
                return source_xpos.replace(":n2:", ":m1.p1:")
            elif ":p2:" in source_xpos:
                return source_xpos.replace(":p2:", ":m1.p1:")
            elif ":p3:" in source_xpos:
                return source_xpos.replace(":p3:", ":m1.p1:")
    elif target_gender == "Fem":
        if ":sg:" in source_xpos:
            if ":m1.m2.m3:" in source_xpos:
                return source_xpos.replace(":m1.m2.m3:", ":f:")
            elif ":m1:" in source_xpos:
                return source_xpos.replace(":m1:", ":f:")
            elif ":m2:" in source_xpos:
                return source_xpos.replace(":m2:", ":f:")
            elif ":m3:" in source_xpos:
                return source_xpos.replace(":m3:", ":f:")
            elif ":n:" in source_xpos:
                return source_xpos.replace(":n:", ":f:")
            elif ":n1.n2:" in source_xpos:
                return source_xpos.replace(":n1.n2:", ":f:")
        elif ":pl:" in source_xpos:
            if ":m1.p1:" in source_xpos:
                return source_xpos.replace(":m1.p1:", ":m2.m3.f.n1.n2.p2.p3:")
            elif ":m1:" in source_xpos:
                return source_xpos.replace(":m1:", ":m2.m3.f.n1.n2.p2.p3:")
    elif target_gender == "Neut":
        if ":sg:" in source_xpos:
            if ":m1.m2.m3:" in source_xpos:
                return source_xpos.replace(":m1.m2.m3:", ":n1.n2:")
            elif ":m1:" in source_xpos:
                return source_xpos.replace(":m1:", ":n1.n2:")
            elif ":m2:" in source_xpos:
                return source_xpos.replace(":m2:", ":n1.n2:")
            elif ":m3:" in source_xpos:
                return source_xpos.replace(":m3:", ":n1.n2:")
            elif ":f:" in source_xpos:
                return source_xpos.replace(":f:", ":n1.n2:")
    return None


QUANTIFIER_LEMMAS = {
    "kilka",
    "kilkaset",
    "kilkanaście",
    "kilkadziesiąt",
    "sporo",
    "mnóstwo",
    "dużo",
    "wiele",
    "więcej",
    "najwięcej",
    "większość",
    "mało",
    "mniej",
    "najmniej",
    "trochę",
    "parę",
    "niewiele",
    "ile",
    "tyle",
}


def token_trees(tree: conllu.TokenTree) -> list[conllu.TokenTree]:
    trees = [tree]
    for child in tree.children:
        trees.extend(token_trees(child))
    return trees


def is_numeral_or_quantifier(token: Token) -> bool:
    return token["upos"] == "NUM" or (
            token["deprel"] == "det" and token["lemma"] in QUANTIFIER_LEMMAS
    )


def extract_children(
        tree: conllu.TokenTree,
        token_predicate: Callable[[Token], bool],
) -> list[Token]:
    return [
        child.token
        for child in tree.children
        if token_predicate(child.token)
    ]


def agrees_with_numeral_subject(number: str | None, nsubj_case: str | None) -> bool:
    return (
            (number == "Sing" and nsubj_case == "Gen")
            or (number == "Plur" and nsubj_case == "Nom")
    )


def match_descendants(tree: conllu.TokenTree, token_predicate):
    matches = []
    for child in tree.children:
        if token_predicate(child.token):
            matches.append(child.token)
        matches.extend(match_descendants(child, token_predicate))
    return matches


def load_sentences(conllu_path: Path, skip_duplicates: bool = True) -> list[conllu.TokenList]:
    sentences: list[conllu.TokenList] = []
    previous_text = None
    with conllu_path.open("r", encoding="utf-8") as handle:
        for sentence in conllu.parse_incr(handle):
            current_text = sentence_text(sentence)
            if skip_duplicates and current_text == previous_text:
                print(f"Skipping duplicate sentence in {conllu_path.name}: {current_text}")
                continue

            metadata = sentence.metadata or {}
            metadata["dataset"] = conllu_path.name
            sentence.metadata = metadata
            sentences.append(sentence)
            previous_text = current_text
    return sentences


def sentence_text(sentence: conllu.TokenList) -> str:
    no_space_until_token_id = None
    multiword_space_after = None
    out: list[str] = []
    for token in sentence:
        token_id = token["id"]
        # conllu parses a CoNLL-U multiword token id like "3-4" as
        # the tuple (3, "-", 4).
        if isinstance(token_id, tuple) and len(token_id) == 3 and token_id[1] == "-":
            # Transforms mutate syntactic component tokens in place, e.g.
            # "3 był" + "4 em" -> "3 byli" + "4 śmy". That leaves the
            # CoNLL-U multiword row "3-4 byłem" outdated and inconsistent, so
            # the tree is invalid if serialized as CoNLL-U. For text output we
            # ignore the old multiword form and print "3 byli" and "4 śmy"
            # without spaces between them.
            # If the multiword row itself has SpaceAfter=No, that applies after
            # the final component token in the range.
            _, _, no_space_until_token_id = token_id
            multiword_space_after = (token.get("misc") or {}).get("SpaceAfter")
            continue
        if not isinstance(token_id, int):
            continue

        out.append(token["form"])
        misc = token.get("misc")
        if no_space_until_token_id is not None and token_id < no_space_until_token_id:
            continue
        if (
                (not misc or misc.get("SpaceAfter") != "No")
                and multiword_space_after != "No"
        ):
            out.append(" ")
        if token_id == no_space_until_token_id:
            no_space_until_token_id = None
            multiword_space_after = None

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
        print(f"Missing form, lemma: {lemma}, target_tag: {target_tag}")
        return False

    form = token.get("form", "")
    if form and form[0].isupper():
        target_form = target_form[:1].upper() + target_form[1:]

    token["form"] = target_form
    token["xpos"] = target_tag
    return True
