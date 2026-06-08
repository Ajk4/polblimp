from __future__ import annotations

import random
from copy import deepcopy
from pathlib import Path
from typing import Callable, Optional

import conllu
import pandas as pd
from conllu import Token, TokenList
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


def change_number_root(sentence: conllu.TokenList, morph_dict: MorphDictionary) -> bool:
    root = sentence.to_tree().token
    return change_number(root, morph_dict)


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


def change_person_root(sentence: conllu.TokenList, morph_dict: MorphDictionary) -> bool:
    root = sentence.to_tree().token
    return change_person(root, morph_dict)


def append_aux_clitic(token: Token, morph_dict: MorphDictionary) -> bool:
    token_form = token["form"]
    source_xpos = token["xpos"]
    if source_xpos.startswith("praet") and not source_xpos.endswith(":agl"):
        agl_xpos = source_xpos + ":agl"
        agl_form = morph_dict.get_form(token["lemma"], agl_xpos)
        if agl_form is not None:
            if token_form and token_form[0].isupper():
                agl_form = agl_form[:1].upper() + agl_form[1:]
            token_form = agl_form

    if random.randint(0, 1) == 0:
        suffix = "śmy" if (token.get("feats") or {}).get("Number") == "Plur" else "m"
    else:
        suffix = "ście" if (token.get("feats") or {}).get("Number") == "Plur" else "ś"

    if suffix in {"m", "ś"} and not token_form.endswith(("a", "o")):
        suffix = "e" + suffix

    token["form"] = token_form + suffix
    return True


def change_person(token: conllu.Token, morph_dict: MorphDictionary) -> bool:
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
    elif token["lemma"] == "być" and source_xpos.startswith("praet"):
        person = random.choice(["pri", "sec", "ter"])
        number = "sg" if ":sg:" in source_xpos else "pl"
        tense = "imperf" if "imperf" in source_xpos else "perf"
        target_xpos = f"bedzie:{number}:{person}:{tense}"
    elif source_xpos.startswith("praet"):
        person = random.choice(["pri", "sec", "ter"])
        number = "sg" if ":sg:" in source_xpos else "pl"
        tense = "imperf" if "imperf" in source_xpos else "perf"
        target_xpos = f"fin:{number}:{person}:{tense}"
    else:
        print(f"Unknown tag={source_xpos}, form={token['form']}")
        return False

    return change_morph(token, morph_dict, target_xpos)

def change_gender_root(
        sentence: conllu.TokenList,
        morph_dict: MorphDictionary,
) -> bool:
    root = sentence.to_tree().token
    return change_gender(root, morph_dict)


def change_gender(root: Token, morph_dict: MorphDictionary) -> bool:
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
        print(f"Unknown tag for gender change, tag={source_xpos}, form={root['form']}")
        return False

    return change_morph(root, morph_dict, target_xpos)

def match_children(tree: conllu.TokenTree, token_predicate):
    matches = []
    for child in tree.children:
        if token_predicate(child.token):
            matches.append(child.token)
    return matches

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
