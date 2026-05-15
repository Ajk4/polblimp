from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import pandas as pd

import conllu

from paradigm.common import load_sentences
from paradigm.morph_dictionary import MorphDictionary
from paradigm.subj_adjectival_number.generator import run_subj_adjectival_number
from paradigm.subj_pred_gender_genitive.generator import run_subj_pred_gender_genitive
from paradigm.subj_pred_gender_numerals.generator import run_subj_pred_gender_numerals
from paradigm.subj_pred_gender_csubj.generator import run_subj_pred_gender_csubj
from paradigm.subj_pred_gender_simple.generator import run_subj_pred_gender_simple
from paradigm.subj_pred_number_csubj.generator import run_subj_pred_number_csubj
from paradigm.subj_pred_number_genitive.generator import run_subj_pred_number_genitive
from paradigm.subj_pred_number_numerals.generator import run_subj_pred_number_numerals
from paradigm.subj_pred_number_simple.generator import run_subj_pred_number_simple
from paradigm.subj_pred_person_csubj.generator import run_subj_pred_person_csubj
from paradigm.subj_pred_person_genitive.generator import run_subj_pred_person_genitive
from paradigm.subj_pred_person_numerals.generator import run_subj_pred_person_numerals
from paradigm.subj_pred_person_simple.generator import run_subj_pred_person_simple
from paradigm.subj_verb_gender_clause.generator import run_subj_verb_gender_clause
from paradigm.subj_verb_gender_genitive.generator import run_subj_verb_gender_genitive
from paradigm.subj_verb_gender_numerals.generator import run_subj_verb_gender_numerals
from paradigm.subj_verb_gender_obj_relative_clause_1.generator import run_subj_verb_gender_obj_relative_clause_1
from paradigm.subj_verb_gender_obj_relative_clause_2.generator import run_subj_verb_gender_obj_relative_clause_2
from paradigm.subj_verb_gender_pp_attractor.generator import run_subj_verb_gender_pp_attractor
from paradigm.subj_verb_gender_simple.generator import run_subj_verb_gender_simple
from paradigm.subj_verb_subj_gender_relative_clause.generator import run_subj_verb_subj_gender_relative_clause
from paradigm.subj_verb_gender_infinitival.generator import run_subj_verb_gender_infinitival
from paradigm.subj_verb_number_clause.generator import run_subj_verb_number_clause
from paradigm.subj_verb_number_infinitival.generator import run_subj_verb_number_infinitival
from paradigm.subj_verb_number_genitive.generator import run_subj_verb_number_genitive
from paradigm.subj_verb_number_numerals.generator import run_subj_verb_number_numerals
from paradigm.subj_verb_number_pp_attractor.generator import run_subj_verb_number_pp_attractor
from paradigm.subj_verb_number_relational_noun.generator import run_subj_verb_number_relational_noun
from paradigm.subj_verb_number_simple.generator import run_subj_verb_number_simple
from paradigm.subj_verb_numerals_1.generator import run_subj_verb_numerals_1
from paradigm.subj_verb_numerals_2.generator import run_subj_verb_numerals_2
from paradigm.subj_verb_person.generator import run_subj_verb_person
from paradigm.subj_verb_person_genitive.generator import run_subj_verb_person_genitive
from paradigm.subj_verb_person_numerals.generator import run_subj_verb_person_numerals
from paradigm.subj_verb_plural_masc.generator import run_subj_verb_plural_masc
from paradigm.subj_verb_plural_non_masc.generator import run_subj_verb_plural_non_masc

QueryRunner = Callable[
    [list[conllu.TokenList], MorphDictionary, Optional[int]],
    pd.DataFrame,
]

PARADIGM_RUNNERS: dict[str, QueryRunner] = {
    "subj_pred_person_simple": run_subj_pred_person_simple,
    "subj_pred_person_csubj": run_subj_pred_person_csubj,
    "subj_pred_gender_simple": run_subj_pred_gender_simple,
    "subj_pred_gender_csubj": run_subj_pred_gender_csubj,
    "subj_pred_gender_numerals": run_subj_pred_gender_numerals,
    "subj_adjectival_number": run_subj_adjectival_number,
    "subj_pred_number_simple": run_subj_pred_number_simple,
    "subj_pred_number_csubj": run_subj_pred_number_csubj,
    "subj_pred_number_numerals": run_subj_pred_number_numerals,
    "subj_pred_person_genitive": run_subj_pred_person_genitive,
    "subj_pred_person_numerals": run_subj_pred_person_numerals,
    "subj_verb_person": run_subj_verb_person,
    # "subj_verb_person_genitive": run_subj_verb_person_genitive,
    "subj_verb_person_numerals": run_subj_verb_person_numerals,
    "subj_verb_number_infinitival": run_subj_verb_number_infinitival,
    "subj_verb_number_genitive": run_subj_verb_number_genitive,
    "subj_pred_number_genitive": run_subj_pred_number_genitive,
    "subj_pred_gender_genitive": run_subj_pred_gender_genitive,
    "subj_verb_number_numerals": run_subj_verb_number_numerals,
    "subj_verb_number_relational_noun": run_subj_verb_number_relational_noun,
    "subj_verb_numerals_1": run_subj_verb_numerals_1,
    "subj_verb_numerals_2": run_subj_verb_numerals_2,
    "subj_verb_gender_simple": run_subj_verb_gender_simple,
    "subj_verb_gender_genitive": run_subj_verb_gender_genitive,
    "subj_verb_gender_numerals": run_subj_verb_gender_numerals,
    "subj_verb_plural_non_masc": run_subj_verb_plural_non_masc,
    "subj_verb_plural_masc": run_subj_verb_plural_masc,
    "subj_verb_gender_clause": run_subj_verb_gender_clause,
    "subj_verb_number_simple": run_subj_verb_number_simple,
    "subj_verb_number_clause": run_subj_verb_number_clause,
    "subj_verb_gender_infinitival": run_subj_verb_gender_infinitival,
    "subj_verb_number_pp_attractor": run_subj_verb_number_pp_attractor,
    "subj_verb_gender_pp_attractor": run_subj_verb_gender_pp_attractor,
    "subj_verb_subj_gender_relative_clause": run_subj_verb_subj_gender_relative_clause,
    "subj_verb_gender_obj_relative_clause_1": run_subj_verb_gender_obj_relative_clause_1,
    "subj_verb_gender_obj_relative_clause_2": run_subj_verb_gender_obj_relative_clause_2,
}


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    matched_sentences = df.attrs.get("matched_sentences")
    assert matched_sentences is not None
    print(f"Wrote {len(df)}/{matched_sentences} rows to {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run standalone CONLLU-based transformations extracted from notebooks."
    )
    parser.add_argument(
        "--data-dir",
        "--data_dir",
        dest="data_dir",
        type=Path,
        default=Path("./data"),
        help="Directory with input .conllu files. All .conllu files in this directory are loaded (default: ./data).",
    )
    parser.add_argument(
        "--morph-dict-path",
        type=Path,
        default=Path("dictionary.v4.csv"),
        help="Path to morphology CSV dictionary.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Directory for output CSV files.",
    )
    parser.add_argument(
        "--paradigm",
        default="all",
        choices=["all", *PARADIGM_RUNNERS.keys()],
        help="Which paradigms(s) to run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum output rows per single filter/transform run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.data_dir.exists():
        raise FileNotFoundError(f"Missing data directory: {args.data_dir}")
    if not args.data_dir.is_dir():
        raise NotADirectoryError(f"Expected directory for --data-dir: {args.data_dir}")
    conllu_paths = sorted(args.data_dir.glob("*.conllu"))
    if not conllu_paths:
        raise FileNotFoundError(f"No .conllu files found in data directory: {args.data_dir}")

    for conllu_path in conllu_paths:
        if not conllu_path.exists():
            raise FileNotFoundError(f"Missing input file: {conllu_path}")
    if not args.morph_dict_path.exists():
        raise FileNotFoundError(f"Missing morphology CSV: {args.morph_dict_path}")

    print(f"Loading morphology dictionary from {args.morph_dict_path} ...")
    morph_dict = MorphDictionary.load(args.morph_dict_path)
    print(f"Loaded morphology dictionary with {len(morph_dict)} lemmas")

    sentences: list[conllu.TokenList] = []
    for conllu_path in conllu_paths:
        print(f"Loading sentences from {conllu_path} ...")
        file_sentences = load_sentences(conllu_path)
        print(f"Loaded {len(file_sentences)} sentences from {conllu_path}")
        sentences.extend(file_sentences)
    print(f"Loaded {len(sentences)} total sentences from {len(conllu_paths)} file(s)")

    if args.paradigm == "all":
        paradigm_names = PARADIGM_RUNNERS.keys()
    else:
        if args.paradigm not in PARADIGM_RUNNERS:
            available = ", ".join(["all", *PARADIGM_RUNNERS.keys()])
            raise ValueError(f"Unknown: {args.paradigm}. Available: {available}")
        paradigm_names = [args.paradigm]

    for paradigm in paradigm_names:
        runner = PARADIGM_RUNNERS[paradigm]
        df = runner(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / f"{paradigm}.csv")


if __name__ == "__main__":
    main()
