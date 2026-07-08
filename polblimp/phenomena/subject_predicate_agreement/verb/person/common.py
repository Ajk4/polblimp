from __future__ import annotations

import random

import conllu
from conllu import Token

from phenomena.common import change_morph
from phenomena.morph_dictionary import MorphDictionary


def append_aux_clitic(token: Token, morph_dict: MorphDictionary) -> bool:
    source_xpos = token["xpos"]
    if not (source_xpos.startswith("praet") or source_xpos.startswith("winien")):
        print(f"Unknown tag for aux clitic append, tag={source_xpos}, form={token['form']}")
        return False

    if ":pl:" in source_xpos:
        target_number = "pl"
    elif ":sg:" in source_xpos:
        target_number = "sg"
    else:
        print(f"Unknown number for aux clitic append, tag={source_xpos}, form={token['form']}")
        return False

    target_person = "pri" if random.randint(0, 1) == 0 else "sec"
    if target_number == "sg" and ":sg:m" in source_xpos:
        target_variant = "wok"
    else:
        target_variant = "nwok"

    host_xpos = source_xpos
    if host_xpos.endswith((":agl", ":nagl")):
        host_xpos = host_xpos.rsplit(":", 1)[0]

    host_form = morph_dict.get_form(token["lemma"], host_xpos)
    if host_form is None:
        print(f"Missing form, lemma: {token['lemma']}, target_tag: {host_xpos}")
        return False

    clitic_xpos = f"aglt:{target_number}:{target_person}:imperf:{target_variant}"
    clitic_form = morph_dict.get_form("być", clitic_xpos)
    if clitic_form is None:
        print(f"Missing form, lemma: być, target_tag: {clitic_xpos}")
        return False

    form = token.get("form", "")
    if form and form[0].isupper():
        host_form = host_form[:1].upper() + host_form[1:]

    token["form"] = host_form + clitic_form
    return True


def change_person(
        root: conllu.TokenTree,
        morph_dict: MorphDictionary,
) -> bool:
    if _is_negated_existence_miec(root):
        return _change_existence_miec_person(root.token, morph_dict)
    return _change_person_no_neg_existence_miec(root.token, morph_dict)


def _change_person_no_neg_existence_miec(
        token: conllu.Token,
        morph_dict: MorphDictionary,
) -> bool:
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
    elif source_xpos.startswith("praet"):
        return append_aux_clitic(token, morph_dict)
    else:
        print(f"Unknown tag={source_xpos}, form={token['form']}")
        return False

    return change_morph(token, morph_dict, target_xpos)


def _change_existence_miec_person(token: conllu.Token, morph_dict: MorphDictionary) -> bool:
    if not (
            token["lemma"] == "mieć"
            and token["form"].lower() == "ma"
            and token["xpos"] == "fin:sg:ter:imperf"
    ):
        print(f"Unexpected existential mieć token, tag={token['xpos']}, form={token['form']}")
        return False

    target_xpos = "fin:sg:pri:imperf" if random.randint(0, 1) == 0 else "fin:sg:sec:imperf"
    target_form = morph_dict.get_form("być", target_xpos)
    if target_form is None:
        print(f"Missing form, lemma: być, target_tag: {target_xpos}")
        return False

    token["form"] = target_form
    token["xpos"] = target_xpos
    return True


def _is_negated_existence_miec(root: conllu.TokenTree) -> bool:
    token = root.token
    if not (
            token["lemma"] == "mieć"
            and token["form"].lower() == "ma"
            and token["xpos"] == "fin:sg:ter:imperf"
    ):
        return False

    has_negation = False
    for child in root.children:
        child_token = child.token
        if child_token["lemma"] == "nie":
            has_negation = True
        child_feats = child_token["feats"] or {}
        if child_token["deprel"] == "nsubj" and child_feats.get("Case") == "Nom":
            return False

    return has_negation
