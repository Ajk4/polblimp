from __future__ import annotations

# Compute snapshot hashes for a registered paradigm.
#
# Examples:
# python polblimp/tools/snapshot_hash.py subj_adjectival_gender
# python polblimp/tools/snapshot_hash.py subj_verb_number_simple --dataset lfg

import argparse
import hashlib
import sys
import tempfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
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
    parser = argparse.ArgumentParser(description="Compute an output snapshot hash for a paradigm.")
    parser.add_argument("paradigm", choices=sorted(PARADIGM_RUNNERS))
    parser.add_argument("--dataset", choices=["lfg", "pdb", "all"], default="all")
    args = parser.parse_args()

    morph_dict = MorphDictionary.load(PACKAGE_ROOT / "dictionary.v4.csv")
    datasets = DATASET_FILENAMES if args.dataset == "all" else (args.dataset,)

    for dataset in datasets:
        sentences = []
        for filename in DATASET_FILENAMES[dataset]:
            sentences.extend(load_sentences(PACKAGE_ROOT / "data" / filename, skip_duplicates=False))

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / f"{args.paradigm}.csv"
            PARADIGM_RUNNERS[args.paradigm](sentences, morph_dict, None).to_csv(output_path, index=False)
            digest = hashlib.sha256(output_path.read_bytes()).hexdigest()
        print(f"{dataset}: {digest}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
