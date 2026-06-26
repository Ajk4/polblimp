from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_gender, match_descendants, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary


def run_subj_verb_gender_attractor(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(matches: dict[str, Token], target_name: str) -> bool:
        target = matches[target_name]
        target_gender = get_target_gender(target, matches["attractor"])
        if target_gender is None:
            return False
        return change_gender(target, morph_dict, target_gender=target_gender)

    # Main verb, singular
    def transform_1a(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_1a(sentence), "root")

    variant_1a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_attractor_1a(s) is not None,
        transform_1a,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__1a",
    )

    # Main verb, plural masculine-personal
    def transform_1b(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_1b(sentence), "root")

    variant_1b = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_attractor_1b(s) is not None,
        transform_1b,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__1b",
    )

    # Main verb, plural non-masculine-personal
    def transform_1c(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_1c(sentence), "root")

    variant_1c = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_attractor_1c(s) is not None,
        transform_1c,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__1c",
    )

    # Copular verb, singular
    def transform_2a(sentence: conllu.TokenList) -> bool:
        return transform(match_subj_verb_gender_attractor_2a(sentence), "cop")

    variant_2a = run_filter_transform(
        sentences,
        lambda s: match_subj_verb_gender_attractor_2a(s) is not None,
        transform_2a,
        limit=limit,
        progress_desc="subj_verb_gender_attractor__2a",
    )

    # Variant 2b have 0 results, variant 2c have 3 results. For now we skip them.

    variants = [variant_1a, variant_1b, variant_1c, variant_2a]
    df = pd.concat(variants)
    df.attrs["matched_sentences"] = sum(df.attrs["matched_sentences"] for df in variants)

    return df


def match_subj_verb_gender_attractor_1a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_main_verb_attractor_match(sentence, target_number="Sing")


def match_subj_verb_gender_attractor_1b(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_main_verb_attractor_match(sentence, target_number="Plur", target_masculine_personal=True)


def match_subj_verb_gender_attractor_1c(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_main_verb_attractor_match(sentence, target_number="Plur", target_masculine_personal=False)


def match_subj_verb_gender_attractor_2a(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return extract_copular_attractor_match(sentence, target_number="Sing")


def extract_main_verb_attractor_match(
        sentence: conllu.TokenList,
        target_number: str,
        target_masculine_personal: bool | None = None,
) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token
    root_feats = root_token["feats"] or {}

    if root_token["upos"] != "VERB":
        return None
    if root_token["deprel"] != "root":
        return None
    if root_feats.get("Number") != target_number:
        return None

    root_gender = root_feats.get("Gender")
    for nsubj in root.children:
        nsubj_token = nsubj.token
        nsubj_feats = nsubj_token["feats"] or {}
        if nsubj_token["deprel"] != "nsubj":
            continue
        if nsubj_feats.get("Gender") != root_gender:
            continue
        if has_conj_child(nsubj):
            continue
        if target_masculine_personal is not None and is_masculine_personal(nsubj_token) != target_masculine_personal:
            continue

        attractor = find_attractor(nsubj, nsubj_token, root_token)
        if attractor is None:
            continue

        return {
            "root": root_token,
            "nsubj": nsubj_token,
            "attractor": attractor,
        }

    return None


def extract_copular_attractor_match(
        sentence: conllu.TokenList,
        target_number: str,
        target_masculine_personal: bool | None = None,
) -> dict[str, Token] | None:
    root = sentence.to_tree()
    root_token = root.token

    if root_token["deprel"] != "root":
        return None
    if root_token["upos"] == "VERB" and root_token["lemma"] != "to":
        return None

    for cop in root.children:
        cop_token = cop.token
        cop_feats = cop_token["feats"] or {}
        if cop_token["upos"] != "AUX":
            continue
        if cop_token["lemma"] in {"to", "by"}:
            continue
        if cop_feats.get("Number") != target_number:
            continue

        cop_gender = cop_feats.get("Gender")
        for nsubj in root.children:
            nsubj_token = nsubj.token
            nsubj_feats = nsubj_token["feats"] or {}
            if nsubj_token["deprel"] not in {"nsubj", "nsubj:pass"}:
                continue
            if nsubj_feats.get("Case") != "Nom":
                continue
            if nsubj_feats.get("Gender") != cop_gender:
                continue
            if has_conj_child(nsubj):
                continue
            if target_masculine_personal is not None and is_masculine_personal(nsubj_token) != target_masculine_personal:
                continue

            attractor = find_attractor(
                nsubj,
                nsubj_token,
                cop_token,
                require_attractor_gender=True,
                ignore_missing_blocker_gender=True,
            )
            if attractor is None:
                continue

            return {
                "root": root_token,
                "cop": cop_token,
                "nsubj": nsubj_token,
                "attractor": attractor,
            }

    return None


def find_attractor(
        nsubj: conllu.TokenTree,
        nsubj_token: Token,
        target_token: Token,
        require_attractor_gender: bool = False,
        ignore_missing_blocker_gender: bool = False,
) -> Token | None:
    for child in nsubj.children:
        attractor = child.token
        if not is_valid_attractor(child, nsubj_token, target_token, require_attractor_gender):
            continue
        if has_intervening_conflicting_descendant(
                nsubj,
                attractor,
                target_token,
                ignore_missing_blocker_gender,
        ):
            continue
        return attractor

    return None


def is_valid_attractor(
        attractor_tree: conllu.TokenTree,
        nsubj_token: Token,
        target_token: Token,
        require_attractor_gender: bool,
) -> bool:
    attractor = attractor_tree.token
    if attractor["upos"] != "NOUN":
        return False
    if attractor["deprel"] not in {"nmod", "nmod:poss", "nmod:arg"}:
        return False
    if require_attractor_gender and (attractor["feats"] or {}).get("Gender") is None:
        return False
    if not is_relational_or_pp_attractor(attractor_tree):
        return False
    if not intervenes_between(nsubj_token, attractor, target_token):
        return False

    target_feats = target_token["feats"] or {}
    target_number = target_feats.get("Number")
    if target_number == "Sing":
        return (attractor["feats"] or {}).get("Gender") != target_feats.get("Gender")
    if target_number == "Plur":
        return is_masculine_personal(attractor) != is_masculine_personal(nsubj_token)
    return False


def is_relational_or_pp_attractor(attractor_tree: conllu.TokenTree) -> bool:
    attractor = attractor_tree.token
    if attractor["deprel"] in {"nmod:poss", "nmod:arg"}:
        return True
    if attractor["deprel"] != "nmod":
        return False

    for child in attractor_tree.children:
        child_token = child.token
        if child_token["deprel"] != "case":
            continue
        child_feats = child_token["feats"] or {}
        if child_token["upos"] != "ADP" and child_feats.get("ExtPos") != "ADP":
            continue
        if child_token["lemma"] == "z" and (attractor["feats"] or {}).get("Case") == "Ins":
            continue
        return True

    return False


def has_intervening_conflicting_descendant(
        nsubj: conllu.TokenTree,
        attractor: Token,
        target_token: Token,
        ignore_missing_gender: bool = False,
) -> bool:
    attractor_id = attractor["id"]
    target_id = target_token["id"]
    if not isinstance(attractor_id, int) or not isinstance(target_id, int):
        return False

    target_number = (target_token["feats"] or {}).get("Number")
    lower_id = min(attractor_id, target_id)
    upper_id = max(attractor_id, target_id)
    blocker_deprels = {"nmod", "nmod:poss", "nmod:arg", "xcomp", "nummod", "conj"}
    blockers = match_descendants(
        nsubj,
        lambda token: (
            token["deprel"] in blocker_deprels
            and isinstance(token["id"], int)
            and lower_id < token["id"] < upper_id
            and (
                (
                    target_number == "Sing"
                    and not (
                        ignore_missing_gender
                        and (token["feats"] or {}).get("Gender") is None
                    )
                    and (token["feats"] or {}).get("Gender") != (attractor["feats"] or {}).get("Gender")
                )
                or (
                    target_number == "Plur"
                    and is_masculine_personal(token) != is_masculine_personal(attractor)
                )
            )
        ),
    )
    return len(blockers) != 0


def intervenes_between(first: Token, middle: Token, last: Token) -> bool:
    first_id = first["id"]
    middle_id = middle["id"]
    last_id = last["id"]
    if not isinstance(first_id, int) or not isinstance(middle_id, int) or not isinstance(last_id, int):
        return False
    return first_id < middle_id < last_id or last_id < middle_id < first_id


def has_conj_child(tree: conllu.TokenTree) -> bool:
    return any(child.token["deprel"] == "conj" for child in tree.children)


def is_masculine_personal(token: Token) -> bool:
    feats = token["feats"] or {}
    return feats.get("SubGender") == "Masc1" or feats.get("Animacy") == "Hum"


def get_target_gender(target: Token, attractor: Token) -> str | None:
    target_feats = target["feats"] or {}
    if target_feats.get("Number") == "Sing":
        return (attractor["feats"] or {}).get("Gender")
    if target_feats.get("Number") == "Plur":
        return "Fem" if is_masculine_personal(target) else "Masc"
    return None
