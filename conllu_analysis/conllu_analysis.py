from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional
import pandas as pd

import conllu

from queries.common import load_sentences
from queries.morph_dictionary import MorphDictionary
from queries.subj_verb_gender_clause import run_subj_verb_gender_clause
from queries.subj_verb_gender_pp_attractor import run_subj_verb_gender_pp_attractor
from queries.subj_verb_gender_simple import run_subj_verb_gender_simple
from queries.subj_verb_gender_infinitival import run_subj_verb_gender_infinitival
from queries.subj_verb_number_clause import run_subj_verb_number_clause
from queries.subj_verb_number_infinitival import run_subj_verb_number_infinitival
from queries.subj_verb_number_pp_attractor import run_subj_verb_number_pp_attractor
from queries.subj_verb_number_relational_noun import run_subj_verb_number_relational_noun
from queries.subj_verb_number_simple import run_subj_verb_number_simple
from queries.subj_verb_numerals_1 import run_subj_verb_numerals_1
from queries.subj_verb_numerals_2 import run_subj_verb_numerals_2
from queries.subj_verb_person import run_subj_verb_person
from queries.subj_verb_plural_masc import run_subj_verb_plural_masc
from queries.subj_verb_plural_non_masc import run_subj_verb_plural_non_masc


def match_predicate_with_pron_nsubj(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    token = root.token
    if token["upos"] != "VERB":
        return None

    for child in root.children:
        child_token = child.token
        if child_token["deprel"] == "nsubj" and child_token["upos"] == "PRON":
            return token

    return None


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
        choices=(
            "all",
            "subj_verb_person",
            "subj_verb_number_infinitival",
            "subj_verb_number_relational_noun",
            "subj_verb_numerals_1",
            "subj_verb_numerals_2",
            "subj_verb_gender_simple",
            "subj_verb_plural_non_masc",
            "subj_verb_plural_masc",
            "subj_verb_gender_clause",
            "subj_verb_number_simple",
            "subj_verb_number_clause",
            "subj_verb_gender_infinitival",
            "subj_verb_number_pp_attractor",
            "subj_verb_gender_pp_attractor",
        ),
        default="all",
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

    if args.task in ("all", "subj_verb_person"):
        df = run_subj_verb_person(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_person.csv")

    if args.task in ("all", "subj_verb_number_infinitival"):
        df = run_subj_verb_number_infinitival(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_number_infinitival.csv")

    if args.task in ("all", "subj_verb_number_relational_noun"):
        df = run_subj_verb_number_relational_noun(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_number_relational_noun.csv")

    if args.task in ("all", "subj_verb_numerals_1"):
        df = run_subj_verb_numerals_1(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_numerals_1.csv")

    if args.task in ("all", "subj_verb_numerals_2"):
        df = run_subj_verb_numerals_2(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_numerals_2.csv")

    if args.task in ("all", "subj_verb_gender_simple"):
        df = run_subj_verb_gender_simple(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_gender_simple.csv")

    if args.task in ("all", "subj_verb_plural_non_masc"):
        df = run_subj_verb_plural_non_masc(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_plural_non_masc.csv")

    if args.task in ("all", "subj_verb_plural_masc"):
        df = run_subj_verb_plural_masc(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_plural_masc.csv")

    if args.task in ("all", "subj_verb_gender_clause"):
        df = run_subj_verb_gender_clause(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_gender_clause.csv")

    if args.task in ("all", "subj_verb_number_simple"):
        df = run_subj_verb_number_simple(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_number_simple.csv")

    if args.task in ("all", "subj_verb_number_clause"):
        df = run_subj_verb_number_clause(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_number_clause.csv")

    if args.task in ("all", "subj_verb_gender_infinitival"):
        df = run_subj_verb_gender_infinitival(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_gender_infinitival.csv")

    if args.task in ("all", "subj_verb_number_pp_attractor"):
        df = run_subj_verb_number_pp_attractor(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_number_pp_attractor.csv")

    if args.task in ("all", "subj_verb_gender_pp_attractor"):
        df = run_subj_verb_gender_pp_attractor(sentences, morph_dict, args.limit)
        write_csv(df, args.output_dir / "subj_verb_gender_pp_attractor.csv")


if __name__ == "__main__":
    main()
