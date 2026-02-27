from __future__ import annotations

import argparse
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import Callable, Optional

import conllu
import pandas as pd
from tqdm import tqdm

POLIFORM_TAG_BY_UD_TAG = {
    "ppron3:sg:nom:m3:ter:akc:npraep": "ppron3:sg:nom:m1.m2.m3:ter:_:_",
    "praet:sg:m1:perf": "praet:sg:m1.m2.m3:perf",
    "praet:sg:m2:perf": "praet:sg:m1.m2.m3:perf",
    "praet:sg:m3:perf": "praet:sg:m1.m2.m3:perf",
    "praet:sg:m1:imperf": "praet:sg:m1.m2.m3:imperf",
    "praet:sg:m2:imperf": "praet:sg:m1.m2.m3:imperf",
    "praet:sg:m3:imperf": "praet:sg:m1.m2.m3:imperf",
}


def load_sentences(conllu_path: Path) -> list[conllu.TokenList]:
    sentences: list[conllu.TokenList] = []
    with conllu_path.open("r", encoding="utf-8") as handle:
        for sentence in conllu.parse_incr(handle):
            sentences.append(sentence)
    return sentences


def load_morph_dict(morph_dict_path: Path) -> pd.DataFrame:
    morph_dict = pd.read_csv(morph_dict_path, dtype={"lemma": "string"})
    morph_dict.set_index("lemma", inplace=True)
    return morph_dict


def has_lemma(morph_dict: pd.DataFrame, lemma: str) -> bool:
    return lemma in morph_dict.index


def get_form(morph_dict: pd.DataFrame, lemma: str, tag: str) -> Optional[str]:
    if not has_lemma(morph_dict, lemma):
        return None

    if tag in POLIFORM_TAG_BY_UD_TAG:
        tag = POLIFORM_TAG_BY_UD_TAG[tag]

    row = morph_dict.loc[lemma]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]

    if tag not in row.index:
        return None

    value = row[tag]
    if pd.notna(value) and value != "":
        return str(value)
    return None


def sentence_text(sentence: conllu.TokenList) -> str:
    out: list[str] = []
    for token in sentence:
        if not isinstance(token["id"], int):
            continue

        out.append(token["form"])
        misc = token.get("misc")
        if not misc or misc.get("SpaceAfter") != "No":
            out.append(" ")

    return "".join(out).rstrip()


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


def change_morph(
    token: conllu.Token,
    morph_dict: pd.DataFrame,
    source_tag: str,
    target_tag: str,
) -> Optional[conllu.Token]:
    xpos = token.get("xpos")
    if xpos != source_tag:
        return None

    lemma = token.get("lemma")
    if not lemma or not has_lemma(morph_dict, lemma):
        return None

    target_form = get_form(morph_dict, lemma, target_tag)
    if target_form is None:
        return None

    form = token.get("form", "")
    if form and form[0].isupper():
        target_form = target_form[:1].upper() + target_form[1:]

    token["form"] = target_form
    token["xpos"] = target_tag
    return token


def match_subj_verb_number_clause(
    sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    token_tree = sentence.to_tree()
    token = token_tree.token
    if token["upos"] == "VERB" and token["deprel"] == "root" and "sg" in token["xpos"]:
        for child in token_tree.children:
            child_xpos = child.token["xpos"].split(":")
            if child.token["upos"] == "VERB" and child.token["deprel"] == "csubj" and "inf" in child_xpos:
                return token
    return None


def match_subj_verb_number_pp_attractor(
    sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    token_tree = sentence.to_tree()
    token = token_tree.token
    token_xpos = token["xpos"].split(":")

    for number in ("sg", "pl"):
        if token["upos"] == "VERB" and token["deprel"] == "root" and number in token_xpos:
            for child in token_tree.children:
                child_xpos = child.token["xpos"].split(":")
                if child.token["upos"] == "NOUN" and child.token["deprel"] == "nsubj" and number in child_xpos:
                    for attractor in child.children:
                        attractor_xpos = attractor.token["xpos"].split(":")
                        other_number = "pl" if number == "sg" else "sg"
                        if other_number in attractor_xpos:
                            for prep in attractor.children:
                                if prep.token["upos"] == "ADP" and prep.token["deprel"] == "case":
                                    return token

    return None


def change_number(token: conllu.Token, morph_dict: pd.DataFrame) -> Optional[conllu.Token]:
    lemma = token.get("lemma")
    if not lemma or not has_lemma(morph_dict, lemma):
        return None

    xpos_raw = token.get("xpos")
    if not xpos_raw:
        return None

    xpos = xpos_raw.split(":")
    for source_number, target_number in (("pl", "sg"), ("sg", "pl")):
        if source_number in xpos:
            source_idx = xpos.index(source_number)
            target_xpos = xpos[:source_idx] + [target_number] + xpos[source_idx + 1 :]
            target_xpos_str = ":".join(target_xpos)
            target_form = get_form(morph_dict, lemma, target_xpos_str)
            if target_form is None:
                return None

            token["form"] = target_form
            token["xpos"] = target_xpos_str
            return token

    return None


def run_filter_transform(
    sentences: list[conllu.TokenList],
    match_token_fn: Callable[[conllu.TokenList], Optional[conllu.Token]],
    transform_inplace_fn: Callable[[conllu.Token], Optional[conllu.Token]],
    limit: Optional[int] = None,
    progress_desc: Optional[str] = None,
    show_progress: bool = True,
) -> pd.DataFrame:
    rows: list[tuple[int, str, str]] = []

    iterator = enumerate(sentences)
    if show_progress:
        iterator = tqdm(
            iterator,
            total=len(sentences),
            desc=progress_desc or "processing",
        )

    for index, sentence in iterator:
        if limit is not None and len(rows) >= limit:
            break

        sentence_copy = deepcopy(sentence)
        token = match_token_fn(sentence_copy)
        if token is None:
            continue

        modified_token = transform_inplace_fn(token)
        if modified_token is None:
            continue

        correct_text = sentence.metadata.get("text") or sentence_text(sentence)
        incorrect_text = sentence_text(sentence_copy)
        rows.append((index, correct_text, incorrect_text))

    return pd.DataFrame(rows, columns=["conllu_index", "correct", "incorrect"])


def combine_outputs(frames: list[pd.DataFrame]) -> pd.DataFrame:
    if not frames:
        return pd.DataFrame(columns=["conllu_index", "correct", "incorrect"])
    combined = pd.concat(frames, ignore_index=True)
    return combined.sort_values("conllu_index").reset_index(drop=True)


def run_person_changes(
    sentences: list[conllu.TokenList],
    morph_dict: pd.DataFrame,
    limit: Optional[int],
    show_progress: bool,
) -> pd.DataFrame:
    results: list[pd.DataFrame] = []

    for aspect in ("perf", "imperf"):
        for source_person in ("pri", "sec", "ter"):
            for target_person in ("pri", "sec", "ter"):
                if source_person == target_person:
                    continue

                source_tag = f"fin:sg:{source_person}:{aspect}"
                target_tag = f"fin:sg:{target_person}:{aspect}"
                transformation = partial(
                    change_morph,
                    morph_dict=morph_dict,
                    source_tag=source_tag,
                    target_tag=target_tag,
                )
                results.append(
                    run_filter_transform(
                        sentences,
                        match_predicate_with_pron_nsubj,
                        transformation,
                        limit=limit,
                        progress_desc=f"person {source_tag} -> {target_tag}",
                        show_progress=show_progress,
                    )
                )

    return combine_outputs(results)


def run_gender_changes(
    sentences: list[conllu.TokenList],
    morph_dict: pd.DataFrame,
    limit: Optional[int],
    show_progress: bool,
) -> pd.DataFrame:
    results: list[pd.DataFrame] = []

    for aspect in ("perf", "imperf"):
        for source_gender in ("f", "m2", "m3"):
            for target_gender in ("f", "m2", "m3"):
                if source_gender == target_gender:
                    continue
                if source_gender.startswith("m") and target_gender.startswith("m"):
                    continue

                source_tag = f"praet:sg:{source_gender}:{aspect}"
                target_tag = f"praet:sg:{target_gender}:{aspect}"
                transformation = partial(
                    change_morph,
                    morph_dict=morph_dict,
                    source_tag=source_tag,
                    target_tag=target_tag,
                )
                results.append(
                    run_filter_transform(
                        sentences,
                        match_predicate_with_pron_nsubj,
                        transformation,
                        limit=limit,
                        progress_desc=f"gender {source_tag} -> {target_tag}",
                        show_progress=show_progress,
                    )
                )

    return combine_outputs(results)


def run_number_clause_changes(
    sentences: list[conllu.TokenList],
    morph_dict: pd.DataFrame,
    limit: Optional[int],
    show_progress: bool,
) -> pd.DataFrame:
    transformation = partial(change_number, morph_dict=morph_dict)
    return run_filter_transform(
        sentences,
        match_subj_verb_number_clause,
        transformation,
        limit=limit,
        progress_desc="number_clause sg<->pl",
        show_progress=show_progress,
    )


def run_pp_attractor_changes(
    sentences: list[conllu.TokenList],
    morph_dict: pd.DataFrame,
    limit: Optional[int],
    show_progress: bool,
) -> pd.DataFrame:
    transformation = partial(change_number, morph_dict=morph_dict)
    return run_filter_transform(
        sentences,
        match_subj_verb_number_pp_attractor,
        transformation,
        limit=limit,
        progress_desc="pp_attractor sg<->pl",
        show_progress=show_progress,
    )


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Wrote {len(df)} rows to {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run standalone CONLLU-based transformations extracted from notebooks."
    )
    parser.add_argument(
        "--conllu-path",
        type=Path,
        default=Path("train_nlprepl-ud.conllu"),
        help="Path to input .conllu file.",
    )
    parser.add_argument(
        "--morph-dict-path",
        type=Path,
        default=Path("dictionary.v3.csv"),
        help="Path to morphology CSV dictionary.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output_old"),
        help="Directory for output CSV files.",
    )
    parser.add_argument(
        "--task",
        choices=("all", "person", "gender", "number_clause", "pp_attractor"),
        default="all",
        help="Which task(s) to run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum output rows per single filter/transform run.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable tqdm progress bars.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    show_progress = not args.no_progress

    if not args.conllu_path.exists():
        raise FileNotFoundError(f"Missing input file: {args.conllu_path}")
    if not args.morph_dict_path.exists():
        raise FileNotFoundError(f"Missing morphology CSV: {args.morph_dict_path}")

    print(f"Loading sentences from {args.conllu_path} ...")
    sentences = load_sentences(args.conllu_path)
    print(f"Loaded {len(sentences)} sentences")

    print(f"Loading morphology dictionary from {args.morph_dict_path} ...")
    morph_dict = load_morph_dict(args.morph_dict_path)
    print(f"Loaded morphology dictionary with {len(morph_dict)} lemmas")

    if args.task in ("all", "person"):
        person_df = run_person_changes(sentences, morph_dict, args.limit, show_progress)
        write_csv(person_df, args.output_dir / "person_changed.csv")

    if args.task in ("all", "gender"):
        gender_df = run_gender_changes(sentences, morph_dict, args.limit, show_progress)
        write_csv(gender_df, args.output_dir / "gender_changed.csv")

    if args.task in ("all", "number_clause"):
        clause_df = run_number_clause_changes(sentences, morph_dict, args.limit, show_progress)
        write_csv(clause_df, args.output_dir / "subj_verb_number_clause.csv")

    if args.task in ("all", "pp_attractor"):
        pp_df = run_pp_attractor_changes(sentences, morph_dict, args.limit, show_progress)
        write_csv(pp_df, args.output_dir / "subj_verb_number_pp_attractor_df.csv")


if __name__ == "__main__":
    main()
