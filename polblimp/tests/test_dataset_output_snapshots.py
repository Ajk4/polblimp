from __future__ import annotations

import hashlib
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

    EXPECTED_HASHES: dict[str, dict[str, str]] = {
        "lfg": {
            "subj_verb_number_csubj": "c22c8758a64e49732f9b00f1f7c747a28532d9403891946b6c245d9b16585675",
            "subj_verb_number_genitive": "fc73cb03b50ce385dd88fbbbf29de52ce602e4778163c6cc9a1d18349dac657b",
            "subj_verb_number_simple": "4082d81f56c872208580246d6189327302629f73c68dbe8ca2da147295016863",
            "subj_verb_person_csubj": "ee8743083a2e18c53337628faa36d2e0ad15d1aad0a6cb3b5ade37230e84d3e0",
            "subj_verb_person_genitive": "a6aa58460d49b4bbada3f94300d8d7dc5b5d898ecd490727b648b10feb0e9626",
            "subj_verb_person_numerals": "aff27f705abef25156577f7da5229709c028069e85fdbb3ade8a2a6f2ed3ac91",
            "subj_verb_person_simple": "bf6a983f4afad6dec37dca96f9005e9c269830736556e7306d59e5d49dbba4d0",
        },
        "pdb": {
            "subj_verb_number_csubj": "eb6f7c3744d595eb325775916cc4ebed664fd67a9fca5f190c476885ad1f3243",
            "subj_verb_number_genitive": "b2d294e7c7cd5f243cabc5fdae9bc4f6c1786c520cc4047a4fce181bf310f60e",
            "subj_verb_number_simple": "4ae711acfbb95ec06bc1d5891bbf7cd6d96b3b5697ea39406e7464ed85cbac26",
            "subj_verb_person_csubj": "b53d5faba14947083052758a371cdd3aadf6355e49f6ef5c65633c69af25924c",
            "subj_verb_person_genitive": "3eead87569fade9ae12bfca3f80ca2692559c6c0e531b6f821536d6d5dfe6853",
            "subj_verb_person_numerals": "c69edb825ccba95453e0e2263d6055915e878b77623c7ba0e6336edf3b94f27f",
            "subj_verb_person_simple": "64374bd43a1f302e045d037ebd17b19c77c8d125dd41dcefbebc0b208607cb2f",
        },
    }

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
                    sentences.extend(load_sentences(path))

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
