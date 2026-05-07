from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import pandas as pd

import conllu

from queries.common import load_sentences
from queries.morph_dictionary import MorphDictionary
from queries.subj_pred_gender_genitive import run_subj_pred_gender_genitive
from queries.subj_pred_gender_csubj import run_subj_pred_gender_csubj
from queries.subj_pred_gender_simple import run_subj_pred_gender_simple
from queries.subj_pred_number_csubj import run_subj_pred_number_csubj
from queries.subj_pred_number_genitive import run_subj_pred_number_genitive
from queries.subj_pred_number_numerals import run_subj_pred_number_numerals
from queries.subj_pred_number_simple import run_subj_pred_number_simple
from queries.subj_pred_person_csubj import run_subj_pred_person_csubj
from queries.subj_pred_person_genitive import run_subj_pred_person_genitive
from queries.subj_pred_person_numerals import run_subj_pred_person_numerals
from queries.subj_pred_person_simple import run_subj_pred_person_simple
from queries.subj_verb_gender_clause import run_subj_verb_gender_clause
from queries.subj_verb_gender_genitive import run_subj_verb_gender_genitive
from queries.subj_verb_gender_numerals import run_subj_verb_gender_numerals
from queries.subj_verb_gender_obj_relative_clause_1 import run_subj_verb_gender_obj_relative_clause_1
from queries.subj_verb_gender_obj_relative_clause_2 import run_subj_verb_gender_obj_relative_clause_2
from queries.subj_verb_gender_pp_attractor import run_subj_verb_gender_pp_attractor
from queries.subj_verb_gender_simple import run_subj_verb_gender_simple
from queries.subj_verb_subj_gender_relative_clause import run_subj_verb_subj_gender_relative_clause
from queries.subj_verb_gender_infinitival import run_subj_verb_gender_infinitival
from queries.subj_verb_number_clause import run_subj_verb_number_clause
from queries.subj_verb_number_infinitival import run_subj_verb_number_infinitival
from queries.subj_verb_number_genitive import run_subj_verb_number_genitive
from queries.subj_verb_number_numerals import run_subj_verb_number_numerals
from queries.subj_verb_number_pp_attractor import run_subj_verb_number_pp_attractor
from queries.subj_verb_number_relational_noun import run_subj_verb_number_relational_noun
from queries.subj_verb_number_simple import run_subj_verb_number_simple
from queries.subj_verb_numerals_1 import run_subj_verb_numerals_1
from queries.subj_verb_numerals_2 import run_subj_verb_numerals_2
from queries.subj_verb_person import run_subj_verb_person
from queries.subj_verb_person_genitive import run_subj_verb_person_genitive
from queries.subj_verb_person_numerals import run_subj_verb_person_numerals
from queries.subj_verb_plural_masc import run_subj_verb_plural_masc
from queries.subj_verb_plural_non_masc import run_subj_verb_plural_non_masc

QueryRunner = Callable[
    [list[conllu.TokenList], MorphDictionary, Optional[int]],
    pd.DataFrame,
]

TASK_RUNNERS: dict[str, QueryRunner] = {
    "subj_pred_person_simple": run_subj_pred_person_simple,
    "subj_pred_person_csubj": run_subj_pred_person_csubj,
    "subj_pred_gender_simple": run_subj_pred_gender_simple,
    "subj_pred_gender_csubj": run_subj_pred_gender_csubj,
    "subj_pred_number_simple": run_subj_pred_number_simple,
    "subj_pred_number_csubj": run_subj_pred_number_csubj,
    "subj_pred_number_numerals": run_subj_pred_number_numerals,
    "subj_pred_person_genitive": run_subj_pred_person_genitive,
    "subj_pred_person_numerals": run_subj_pred_person_numerals,
    "subj_verb_person": run_subj_verb_person,
    "subj_verb_person_genitive": run_subj_verb_person_genitive,
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
        "--task",
        default="all",
        choices=["all", *TASK_RUNNERS.keys()],
        help="Which task(s) to run.",
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

    if args.task == "all":
        task_names = TASK_RUNNERS.keys()
    else:
        if args.task not in TASK_RUNNERS:
            available = ", ".join(["all", *TASK_RUNNERS.keys()])
            raise ValueError(f"Unknown task: {args.task}. Available tasks: {available}")
        task_names = [args.task]

    for task_name in task_names:
        runner = TASK_RUNNERS[task_name]
        df = runner(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / f"{task_name}.csv")


if __name__ == "__main__":
    main()
