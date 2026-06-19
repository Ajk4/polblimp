from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_morph, run_filter_transform
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_number.generator import (
    match_subj_adjectival_number,
)


def run_subj_adjectival_case(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = match_subj_adjectival_case(sentence)
        assert matches is not None, "Matched sentences are supposed to be filtered first"

        target_xpos = get_target_case_xpos(matches["root"])
        if target_xpos is None:
            return False
        root_form = matches["root"]["form"]
        changed = change_morph(matches["root"], morph_dict, target_xpos)
        return changed and matches["root"]["form"] != root_form

    return run_filter_transform(
        sentences,
        lambda s: match_subj_adjectival_case(s) is not None,
        transform,
        limit=limit,
        progress_desc="subj_adjectival_case",
    )


def match_subj_adjectival_case(sentence: conllu.TokenList) -> dict[str, Token] | None:
    return match_subj_adjectival_number(sentence)


def get_target_case_xpos(token: Token) -> str | None:
    source_xpos = token["xpos"]
    if ":nom:" in source_xpos:
        return source_xpos.replace(":nom:", ":gen:")
    if ":gen:" in source_xpos:
        return source_xpos.replace(":gen:", ":nom:")

    print(f"Unknown tag for case change, tag={source_xpos}, form={token['form']}")
    return None
