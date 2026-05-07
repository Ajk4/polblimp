
"""
subj_pred_number_numerals
With numerals <5, the copula agrees with the noun (plural and verb’s gender).
With numerals ≥5 (and for masculine <5 – in case of the numeral in accusative and noun in genitive), the default agreement is 3 singular neuter.

For small numerals (nsubj in nominative): Change the number of $cop and if $root is an adjective –  the number of $root.
For large numerals (nsubj in genitive): Change the number of $cop. or more?

Examples:
 Ci dwaj byli na siebie specjalnie uczuleni.
*Ci dwaj był na siebie specjalnie uczulony.

 jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanych.
*są na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanych.
* jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywanej. ?
* jest na niej 250 szopek nigdy dotąd poza Betlejem niepokazywana. ?


Query:
a-node $root := [
  !tag = 'VERB',
  deprel = 'root',

  child a-node $nsubj := [
    deprel ~ '^(nsubj|nsubj:pass)$',

    child a-node $num := [
    tag = 'NUM',
    ],
  ],

  child a-node $cop :=[
    tag = 'AUX',
    !lemma = 'to',
    !lemma = 'by'
  ]
]

"""

from __future__ import annotations

from typing import Optional

import conllu
import pandas as pd

from .common import change_number, run_filter_transform
from .morph_dictionary import MorphDictionary
from .subj_pred_person_numerals import (
    extract_subj_pred_person_numerals as extract_subj_pred_number_numerals,
    match_subj_pred_person_numerals as match_subj_pred_number_numerals,
)


def run_subj_pred_number_numerals(
        sentences: list[conllu.TokenList],
        morph_dict: MorphDictionary,
        limit: Optional[int],
) -> pd.DataFrame:
    def transform(sentence: conllu.TokenList) -> bool:
        matches = extract_subj_pred_number_numerals(sentence)
        assert matches is not None, "Matched senteces are supposed to be filtered first"

        nsubj_feats = matches["nsubj"]["feats"] or {}
        nsubj_case = nsubj_feats.get("Case")

        if nsubj_case == "Nom":
            if matches["root"]["upos"] == "ADJ":
                return change_number(matches["cop"], morph_dict) and change_number(matches["root"], morph_dict)
            else:
                return change_number(matches["cop"], morph_dict)
        if nsubj_case == "Gen":
            return change_number(matches["cop"], morph_dict)

        return False

    return run_filter_transform(
        sentences,
        match_subj_pred_number_numerals,
        transform,
        limit=limit,
        progress_desc="subj_pred_number_numerals",
    )
