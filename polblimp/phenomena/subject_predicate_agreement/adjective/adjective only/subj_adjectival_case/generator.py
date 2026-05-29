from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from phenomena.common import change_number, match_descendants, run_filter_transform, change_morph
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_number.generator import match_subj_adjectival_number, extract_subj_adjectival_number


def run_subj_adjectival_case(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_adjectival_number(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"

        root = matches['root']
        tag = root['xpos']

        if 'nom' in tag:
            target_tag = tag.replace('nom', 'gen')
        elif 'gen' in tag:
            target_tag = tag.replace('gen', 'nom')
        else:
            print(f"Ignoring tag '{tag}' for root form '{root['form']}' which is neither nom or gen")
            return False

        return change_morph(matches["root"], morph_dict, target_tag)

    return run_filter_transform(
        sentences,
        match_subj_adjectival_number,
        transform,
        limit=limit,
        progress_desc="subj_adjectival_case",
    )

