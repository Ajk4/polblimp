from __future__ import annotations

# Update snapshot hashes for registered paradigms.
#
# Examples:
# python polblimp/tests/refresh_snapshots.py
# python polblimp/tests/refresh_snapshots.py subj_adjectival_gender
# python polblimp/tests/refresh_snapshots.py subj_verb_number_simple --dataset lfg

import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS_PATH = PACKAGE_ROOT / "tests" / "dataset_output_snapshots.json"
sys.path.insert(0, str(PACKAGE_ROOT))

from generate import PARADIGM_RUNNERS  # noqa: E402
from phenomena.common import load_sentences  # noqa: E402
from phenomena.morph_dictionary import MorphDictionary  # noqa: E402


DATASET_FILENAMES = {
    "lfg": (
        "pl_lfg-ud-train.conllu",
        "pl_lfg-ud-dev.conllu",
        "pl_lfg-ud-test.conllu",
    ),
    "pdb": (
        "pl_pdb-ud-train.conllu",
        "pl_pdb-ud-dev.conllu",
        "pl_pdb-ud-test.conllu",
    ),
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Update output snapshot hashes.")
    parser.add_argument("paradigm", nargs="?", choices=["all", *sorted(PARADIGM_RUNNERS)], default="all")
    parser.add_argument("--dataset", choices=["lfg", "pdb", "all"], default="all")
    parser.add_argument("--output", type=Path, default=SNAPSHOTS_PATH)
    args = parser.parse_args()

    morph_dict = MorphDictionary.load(PACKAGE_ROOT / "dictionary.v4.csv")
    datasets = DATASET_FILENAMES.keys() if args.dataset == "all" else (args.dataset,)
    paradigms = PARADIGM_RUNNERS.keys() if args.paradigm == "all" else (args.paradigm,)
    snapshots = json.loads(args.output.read_text()) if args.output.exists() else {}

    for dataset in datasets:
        snapshots.setdefault(dataset, {})
        sentences = []
        for filename in DATASET_FILENAMES[dataset]:
            sentences.extend(load_sentences(PACKAGE_ROOT / "data" / filename, skip_duplicates=False))

        for paradigm in paradigms:
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / f"{paradigm}.csv"
                PARADIGM_RUNNERS[paradigm](sentences, morph_dict, None).to_csv(output_path, index=False)
                digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
            snapshots[dataset][paradigm] = digest
            print(f"{paradigm}: {dataset}={digest}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(snapshots, indent=2) + "\n")
    print(f"Updated {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
