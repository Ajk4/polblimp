from __future__ import annotations

from pathlib import Path
from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_gender
from phenomena.morph_dictionary import MorphDictionary
from phenomena.pmltq import Match, QueryVariant, run_query_transforms


def run_subj_verb_gender_genitive(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(_sentence: conllu.TokenList, match: Match) -> bool:
        return change_gender(match["root"], morph_dict)

    return run_query_transforms(
        sentences,
        Path(__file__).with_name("queries"),
        (QueryVariant("1a", ("root",), transform, "subj_verb_gender_genitive__1a"),),
        limit,
    )
