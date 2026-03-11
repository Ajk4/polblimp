from __future__ import annotations

import argparse
from copy import deepcopy
from functools import partial
from pathlib import Path
from typing import Callable, Optional

import conllu
import pandas as pd
from conllu import TokenTree
from tqdm import tqdm

# POLIFORM_TAG_BY_UD_TAG = {
#     'ppron3:sg:nom:m3:ter:akc:npraep': 'ppron3:sg:nom:m1.m2.m3:ter:_:_',
#     'praet:sg:m1:perf': 'praet:sg:m1.m2.m3:perf',
#     'praet:sg:m2:perf': 'praet:sg:m1.m2.m3:perf',
#     'praet:sg:m3:perf': 'praet:sg:m1.m2.m3:perf',
#     'praet:sg:m1:imperf': 'praet:sg:m1.m2.m3:imperf',
#     'praet:sg:m2:imperf': 'praet:sg:m1.m2.m3:imperf',
#     'praet:sg:m3:imperf': 'praet:sg:m1.m2.m3:imperf',
#     'praet:pl:m1:perf': 'praet:pl:m1.p1:perf',
#     'praet:pl:n:perf': 'praet:pl:m2.m3.f.n1.n2.p2.p3:perf',
#     'praet:pl:n:imperf': 'praet:pl:m2.m3.f.n1.n2.p2.p3:imperf',
#     'praet:pl:f:perf': 'praet:pl:m2.m3.f.n1.n2.p2.p3:imperf.perf',
#     'praet:pl:f:imperf': 'praet:pl:m2.m3.f.n1.n2.p2.p3:imperf.perf',
# }

def is_subtag(tag: str, supertag:str) -> bool:
    if tag == supertag:
        return True

    tag_parts = tag.split(":")
    supertag_parts = supertag.split(":")

    if len(tag_parts) != len(supertag_parts):
        return False

    for tag_part, supertag_part in zip(tag_parts, supertag_parts):
        supertag_part_options = supertag_part.split(".")
        if tag_part not in supertag_part_options:
            return False
    return True

def load_sentences(conllu_path: Path, limit=None) -> list[conllu.TokenList]:
    sentences: list[conllu.TokenList] = []
    with conllu_path.open("r", encoding="utf-8") as handle:
        for sentence in conllu.parse_incr(handle):
            sentences.append(sentence)
            if limit is not None:
                if len(sentences) >= limit:
                    break
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

    row = morph_dict.loc[lemma]

    if ':n:' in tag:  # FIXME HACK
        tag = tag.replace(":n:", ":n1:")

    for col, val in row.items():
        if pd.notna(val) and val != "" and is_subtag(tag, col):
            return str(val)
    else:
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
        target_tag: str,
) -> Optional[conllu.Token]:
    lemma = token.get("lemma")
    if not lemma or not has_lemma(morph_dict, lemma):
        print("Missing lemma", lemma)
        return None

    target_form = get_form(morph_dict, lemma, target_tag)
    if target_form is None:
        print(f"Missing form, lemma: {lemma}, form: {target_tag}")
        # get_form(morph_dict, lemma, target_tag)  # debug
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
            if child.token["upos"] == "VERB" and child.token["deprel"] == "csubj" and "inf" not in child_xpos:
                return token
    return None


def match_subj_verb_number_pp_attractor(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()

    if root.token["upos"] != "VERB":
        return None

    root_number = root.token["feats"].get("Number")

    for nsubj in root.children:
        if nsubj.token["upos"] != "NOUN":
            continue
        if nsubj.token["deprel"] != "nsubj":
            continue

        nsubj_feats = nsubj.token["feats"]
        if nsubj_feats.get("Number", "") != root_number:
            continue

        def match_attractor(token: conllu.Token) -> bool:
            return token['deprel'] in {'nmod', "nmod:poss", "xcomp", "conj"}

        attractors = match_descendants(nsubj, match_attractor)
        if len(attractors) != 1:
            continue

        for attractor in nsubj.children:
            if attractor.token["upos"] != "NOUN":
                continue
            if attractor.token["deprel"] != "nmod":
                continue

            attractor_feats = attractor.token["feats"]
            if attractor_feats.get("Number", "") == root_number:
                continue

            for prep in attractor.children:
                if prep.token["upos"] != "ADP":
                    continue
                if prep.token["deprel"] != "case":
                    continue

                if prep.token['lemma'] == 'z' and attractor_feats.get("Case") != "Ins":
                    return root.token
                if prep.token['lemma'] != 'z':
                    return root.token

    return None


def run_filter_transform(
        sentences: list[conllu.TokenList],
        match_token_fn: Callable[[conllu.TokenList], Optional[conllu.Token]],
        transform_inplace_fn: Callable[[conllu.Token], Optional[conllu.Token]],
        limit: Optional[int] = None,
        progress_desc: Optional[str] = None,
) -> pd.DataFrame:
    rows: list[tuple[int, str, str]] = []

    iterator = tqdm(
        enumerate(sentences),
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


def run_subj_verb_number_simple(
        sentences: list[conllu.TokenList],
        morph_dict: pd.DataFrame,
        limit: Optional[int],
) -> pd.DataFrame:
    # TODO transformation
    def transformation(token: conllu.Token) -> Optional[conllu.Token]:
        # TODO DRY
        source_xpos = token["xpos"]
        if 'pl' in source_xpos:
            target_xpos = source_xpos.replace('pl', 'sg')
        elif 'sg' in source_xpos:
            target_xpos = source_xpos.replace('sg', 'pl')
        else:
            print("Unknown tag", source_xpos)
            return None

        return change_morph(token, morph_dict, target_xpos)

    return run_filter_transform(
        sentences,
        match_subj_verb_number_simple,
        transformation,
        limit=limit,
        progress_desc=f"run_subj_verb_number_simple",
    )


def run_subj_verb_number_clause(
        sentences: list[conllu.TokenList],
        morph_dict: pd.DataFrame,
        limit: Optional[int],
) -> pd.DataFrame:
    # TODO transformation
    def transformation(token: conllu.Token) -> Optional[conllu.Token]:
        source_xpos = token["xpos"]

        if 'pl' in source_xpos:
            target_xpos = source_xpos.replace('pl', 'sg')
        elif 'sg' in source_xpos:
            target_xpos = source_xpos.replace('sg', 'pl')
        else:
            print("Unknown tag", source_xpos)
            return None

        return change_morph(token, morph_dict, target_xpos)

    return run_filter_transform(
        sentences,
        match_subj_verb_number_clause,  # TODO CHECK
        transformation,
        limit=limit,
        progress_desc=f"run_subj_verb_number_clause",
    )


def match_subj_verb_number_clause2(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    if root.token["upos"] != "VERB":
        return None

    root_feats = root.token['feats']
    if root_feats.get("Number", "") != 'Sing':
        return None

    for child in root.children:
        child_feats = child.token['feats']
        if child.token["upos"] == "VERB" and child.token["deprel"] == "csubj" and child_feats.get("VerbForm",
                                                                                                  "") != "Inf":
            return root.token

    return None


def match_subj_verb_number_simple(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    if root.token["upos"] != "VERB":
        return None

    root_feats = root.token['feats']
    if 'Number' not in root_feats:
        return None

    for child in root.children:
        child_token = child.token

        if child_token["upos"] != "NOUN":
            continue

        if child_token["deprel"] != "nsubj":
            continue

        child_feats = child_token['feats']
        if child_feats.get('Number', "") != root_feats['Number']:
            continue

        def descendant_predicate(token: conllu.Token) -> bool:
            feats = token['feats']
            if feats is None:
                return False

            return (token['deprel'] in {"nmod", "nmod:poss", "xcomp", "conj", "nummod"})

        unwanted_descendants = match_descendants(child, descendant_predicate)
        if len(unwanted_descendants) == 0:
            return root.token

    return None


def match_descendants(tree: conllu.TokenTree, token_predicate):
    matches = []
    for child in tree.children:
        if token_predicate(child.token):
            matches.append(child.token)
        matches.extend(match_descendants(child, token_predicate))
    return matches


def run_subj_verb_number_pp_attractor(
        sentences: list[conllu.TokenList],
        morph_dict: pd.DataFrame,
        limit: Optional[int],
) -> pd.DataFrame:
    # TODO transformation

    def transformation(token: conllu.Token) -> Optional[conllu.Token]:
        # TODO
        return token

    # transformation = partial(change_number, morph_dict=morph_dict)

    return run_filter_transform(
        sentences,
        match_subj_verb_number_pp_attractor,
        transformation,
        limit=limit,
        progress_desc="subj_verb_number_pp_attractor",
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
        default=Path("dictionary.v3.csv"),
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
        # TODO remove gender, number_clause
        choices=("all", "subj_verb_number_simple", "subj_verb_number_clause", "subj_verb_gender_infinitival",
                 "subj_verb_number_pp_attractor"),
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


def run_subj_verb_gender_infinitival(
        sentences: list[conllu.TokenList],
        morph_dict: pd.DataFrame,
        limit: Optional[int],
) -> pd.DataFrame:
    # TODO transformation
    def transformation(token: conllu.Token) -> Optional[conllu.Token]:
        # TODO
        return token

    return run_filter_transform(
        sentences,
        match_subj_verb_gender_infinitival,
        transformation,
        limit=limit,
        progress_desc=f"subj_verb_number_clause",
    )


def match_subj_verb_gender_infinitival(
        sentence: conllu.TokenList,
) -> Optional[conllu.Token]:
    root = sentence.to_tree()
    root_feats = root.token['feats']
    if (root.token["upos"] == "VERB" and root.token["deprel"] == "root" and
            root_feats.get("Number", "") == 'Sing' and root_feats.get("Gender", "") == "Neut"):
        for infinitive in root.children:
            infinitive_feats = infinitive.token['feats']
            if infinitive.token["upos"] == "VERB" and infinitive.token["deprel"] == "csubj" and infinitive_feats.get(
                    'VerbForm', "") == "Inf":
                return root.token
    return None


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
    morph_dict = load_morph_dict(args.morph_dict_path)
    print(f"Loaded morphology dictionary with {len(morph_dict)} lemmas")

    sentences: list[conllu.TokenList] = []
    for conllu_path in conllu_paths:
        print(f"Loading sentences from {conllu_path} ...")
        file_sentences = load_sentences(conllu_path)
        print(f"Loaded {len(file_sentences)} sentences from {conllu_path}")
        sentences.extend(file_sentences)
    print(f"Loaded {len(sentences)} total sentences from {len(conllu_paths)} file(s)")

    if args.task in ("all", "subj_verb_number_simple"):
        person_df = run_subj_verb_number_simple(sentences, morph_dict, args.limit)
        write_csv(person_df, args.output_dir / "subj_verb_number_simple.csv")

    if args.task in ("all", "subj_verb_number_clause"):
        person_df = run_subj_verb_number_clause(sentences, morph_dict, args.limit)
        write_csv(person_df, args.output_dir / "subj_verb_number_clause.csv")

    if args.task in ("all", "subj_verb_gender_infinitival"):
        person_df = run_subj_verb_gender_infinitival(sentences, morph_dict, args.limit)
        write_csv(person_df, args.output_dir / "subj_verb_gender_infinitival.csv")

    if args.task in ("all", "subj_verb_number_pp_attractor"):
        pp_df = run_subj_verb_number_pp_attractor(sentences, morph_dict, args.limit)
        write_csv(pp_df, args.output_dir / "subj_verb_number_pp_attractor.csv")


if __name__ == "__main__":
    main()
