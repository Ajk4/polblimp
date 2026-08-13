from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from generate import PARADIGM_RUNNERS
from phenomena.common import load_sentences
from phenomena.morph_dictionary import MorphDictionary


class TestDatasetOutputSnapshots(unittest.TestCase):
    DATASET_FILENAMES: dict[str, tuple[str, ...]] = {
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

    EXPECTED_HASHES: dict[str, dict[str, str]] = json.loads(
        Path(__file__).with_name("dataset_output_snapshots.json").read_text()
    )

    def test_generated_outputs_match_snapshots(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        data_dir = repo_root / "data"
        morph_dict = MorphDictionary.load(repo_root / "dictionary.v4.csv")

        for dataset_name, filenames in self.DATASET_FILENAMES.items():
            with self.subTest(dataset=dataset_name):
                sentences = []
                for filename in filenames:
                    path = data_dir / filename
                    if not path.exists():
                        raise FileNotFoundError(f"Missing {dataset_name} data file: {path}")
                    sentences.extend(load_sentences(path, skip_duplicates=False))

                expected_hashes = self.EXPECTED_HASHES[dataset_name]
                self.assertEqual(set(expected_hashes), set(PARADIGM_RUNNERS))

                with tempfile.TemporaryDirectory() as tmpdir:
                    output_dir = Path(tmpdir)
                    for paradigm_name, runner in PARADIGM_RUNNERS.items():
                        with self.subTest(dataset=dataset_name, paradigm=paradigm_name):
                            output_path = output_dir / f"{paradigm_name}.csv"
                            df = runner(sentences, morph_dict, None)
                            df.to_csv(output_path, index=False)

                            actual_hash = hashlib.sha256(output_path.read_bytes()).hexdigest()
                            expected_hash = expected_hashes[paradigm_name]
                            self.assertEqual(expected_hash, actual_hash)
