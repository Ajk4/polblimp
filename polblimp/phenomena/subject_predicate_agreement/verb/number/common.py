from __future__ import annotations

import conllu
from conllu import Token

from phenomena.common import change_morph, change_number, remove_token_preserving_spacing
from phenomena.morph_dictionary import MorphDictionary


def change_number_with_aux_clitic(
        sentence: conllu.TokenList,
        host: Token,
        auxclitic: Token,
        source_person: str,
        morph_dict: MorphDictionary,
) -> bool:
    if not change_number(host, morph_dict):
        return False

    if not change_aux_clitic_number(host, auxclitic, source_person, morph_dict):
        return False

    if ":sg:m" in host["xpos"]:
        agglutinative_form = morph_dict.get_form(host["lemma"], f"{host['xpos']}:agl")
        if agglutinative_form is not None:
            if host["form"] and host["form"][0].isupper():
                agglutinative_form = agglutinative_form[:1].upper() + agglutinative_form[1:]
            host["form"] = agglutinative_form

    host["form"] += auxclitic["form"]
    return remove_token_preserving_spacing(sentence, auxclitic)


def change_aux_clitic_number(
        host: Token,
        auxclitic: Token,
        source_person: str,
        morph_dict: MorphDictionary,
) -> bool:
    target_number = {"Sing": "pl", "Plur": "sg"}.get((auxclitic["feats"] or {}).get("Number"))
    target_person = {"1": "pri", "2": "sec"}.get(source_person)
    if target_number is None or target_person is None:
        print(f"Unknown aux clitic tag={auxclitic['xpos']}, form={auxclitic['form']}")
        return False

    target_variant = "nwok"
    if target_number == "sg":
        if host["xpos"].startswith("praet:sg:m"):
            target_variant = "wok"
        elif not (host["xpos"].startswith("praet:sg:f:") or host["xpos"].startswith("praet:sg:n")):
            print(f"Unknown host tag for aux clitic, tag={host['xpos']}, form={host['form']}")
            return False

    target_xpos = f"aglt:{target_number}:{target_person}:imperf:{target_variant}"
    return change_morph(auxclitic, morph_dict, target_xpos)
