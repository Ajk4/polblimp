from __future__ import annotations

import argparse
from collections.abc import Callable
from pathlib import Path
from typing import Optional

import pandas as pd

import conllu

from phenomena.common import load_sentences
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_simple.generator import \
    run_subj_verb_person_simple
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_genitive.generator import \
    run_subj_verb_person_genitive
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_numerals.generator import \
    run_subj_verb_person_numerals

QueryRunner = Callable[
    [list[conllu.TokenList], MorphDictionary, Optional[int]],
    pd.DataFrame,
]

PARADIGM_RUNNERS: dict[str, QueryRunner] = {
    "subj_verb_person_genitive": run_subj_verb_person_genitive,
    "subj_verb_person_numerals": run_subj_verb_person_numerals,
    "subj_verb_person_simple": run_subj_verb_person_simple,
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
