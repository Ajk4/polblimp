from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd
from conllu import Token

from phenomena.common import change_morph
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_number.generator import (
    match_subj_adjectival_number,
)


def run_subj_adjectival_case(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(_sentence: conllu.TokenList, match: Match) -> bool:
        if (match["root"]["feats"] or {}).get("Case") not in {"Nom", "Gen"}:
            return False

        target_xpos = get_target_case_xpos(match["root"])
        if target_xpos is None:
            return False
        return change_morph(match["root"], morph_dict, target_xpos)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (QueryVariant("1a", ("root",), transform, "subj_adjectival_case"),),
        limit,
    )


def match_subj_adjectival_case(sentence: conllu.TokenList) -> list[dict[str, Token]]:
    return match_subj_adjectival_number(sentence)


def get_target_case_xpos(token: Token) -> str | None:
    source_xpos = token["xpos"]
    if ":nom:" in source_xpos:
        return source_xpos.replace(":nom:", ":gen:")
    if ":gen:" in source_xpos:
        return source_xpos.replace(":gen:", ":nom:")

    print(f"Unknown tag for case change, tag={source_xpos}, form={token['form']}")
    return None
