from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import run_filter_transform, change_morph
from .morph_dictionary import MorphDictionary, is_subtag


def run_subj_verb_gender_obj_relative_clause_1(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_verb_gender_obj_relative_clause(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"
        token_to_change = matches['root']
        target_gender = matches['subj_rel']['feats']['Gender']
        return change_gender_to(token_to_change, morph_dict, target_gender)

    return run_filter_transform(
        sentences,
        match_subj_verb_gender_obj_relative_clause,
        transform,
        limit=limit,
        progress_desc="subj_verb_gender_obj_relative_clause_1",
    )


def change_gender_to(token: conllu.Token, morph_dict: MorphDictionary, target_gender) -> bool:
    assert target_gender in {"Neut", "Masc", "Fem"}

    source_xpos = token["xpos"]

    if source_xpos in {"fin:sg:ter:imperf", "fin:sg:ter:perf"}:
        print(f"Ignoring {source_xpos} with '{token['form']}' form")
        return False

    if target_gender == "Neut":
        if is_subtag(source_xpos, "praet:sg:f.m1.m2.m3:imperf"):
            target_xpos = "praet:sg:n1.n2:imperf"
        elif is_subtag(source_xpos, "praet:sg:f.m1.m2.m3:perf"):
            target_xpos = "praet:sg:n1:perf"
        elif is_subtag(source_xpos, "praet:pl:f.m1.m2.m3:imperf"):
            target_xpos = "praet:pl:n:imperf"
        elif is_subtag(source_xpos, "praet:pl:f.m1.m2.m3:perf"):
            target_xpos = "praet:pl:n:perf"
        else:
            assert False, f"source_xpos: {source_xpos}"
    elif target_gender == "Fem":
        if is_subtag(source_xpos, "praet:sg:n.n1.n2.m1.m2.m3:imperf"):
            target_xpos = "praet:sg:f:imperf"
        elif is_subtag(source_xpos, "praet:pl:m1.n:imperf"):
            target_xpos = "praet:pl:f:imperf"
        elif is_subtag(source_xpos, "praet:sg:n.n1.n2.m1.m2.m3:perf"):
            target_xpos = "praet:sg:f:perf"
        elif is_subtag(source_xpos, "praet:pl:n.n1.n2.m1.m2.m3:perf"):
            target_xpos = "praet:pl:f:perf"
        else:
            assert False, f"source_xpos: {source_xpos}"
    elif target_gender == "Masc":
        if is_subtag(source_xpos, "praet:sg:f.n1.n2:imperf"):
            target_xpos = "praet:sg:m1.m2.m3:imperf"
        elif is_subtag(source_xpos, "praet:pl:m2.m3.f.n1.n2:imperf"):
            target_xpos = "praet:pl:m1:imperf"
        elif is_subtag(source_xpos, "praet:sg:n:perf"):
            target_xpos = "praet:sg:m1:perf"
        elif is_subtag(source_xpos, "praet:sg:n:imperf"):
            target_xpos = "praet:sg:m1:imperf"
        else:
            assert False, f"form: {token['form']}, source_xpos: {source_xpos}"
    else:
        assert False, f"target_gender: {target_gender}"

    return change_morph(token, morph_dict, target_xpos)


def match_subj_verb_gender_obj_relative_clause(
        sentence: conllu.TokenList,
) -> bool:
    return extract_subj_verb_gender_obj_relative_clause(sentence) is not None


def extract_subj_verb_gender_obj_relative_clause(
        sentence: conllu.TokenList,
) -> Optional[dict[str, conllu.Token]]:
    root = sentence.to_tree()
    root_feats = root.token["feats"] or {}
    root_gender = root_feats.get("Gender")
    root_number = root_feats.get("Number")

    if root.token["upos"] != "VERB":
        return None
    if root.token["deprel"] != "root":
        return None

    for subj_main in root.children:
        subj_main_feats = subj_main.token["feats"] or {}
        if subj_main.token["deprel"] != "nsubj":
            continue
        if subj_main.token["upos"] != "NOUN":
            continue
        if subj_main_feats.get("Gender") != root_gender:
            continue
        if subj_main_feats.get("Number") != root_number:
            continue

        for relcl in subj_main.children:
            if relcl.token["deprel"] != "acl:relcl":
                continue
            if relcl.token["upos"] != "VERB":
                continue

            for subj_rel in relcl.children:
                subj_rel_feats = subj_rel.token["feats"] or {}
                if subj_rel.token["deprel"] != "nsubj":
                    continue
                if subj_rel.token["upos"] != "NOUN":
                    continue
                if subj_rel_feats.get("Gender") == subj_main_feats.get("Gender"):
                    continue
                return {
                    "root": root.token,
                    "subj_main": subj_main.token,
                    "relcl": relcl.token,
                    "subj_rel": subj_rel.token,
                }

    return None
