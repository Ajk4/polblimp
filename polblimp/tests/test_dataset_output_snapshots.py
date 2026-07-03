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
            "subj_adjectival_case": "a8b012e89f5cd46ab4d3746a9970d47f9c8dfbbd20946887a01cae9879dc0857",
            "subj_adjectival_gender": "cbf1851149e496c1739f6b51c944a90c724c719232140c63190e51746871a949",
            "subj_adjectival_gender_cop": "747ef327a851734e36cf717155b3fe2379838cea57a1c69eec80b110c29074f3",
            "subj_adjectival_number": "bbbef31f1847a4deee56b1e165515f6d0b5e45280d06087032e93a7a0b7e0132",
            "subj_adjectival_number_cop": "34105fff5e538b1c7649dc3de8a097117f7f6e7cc1e235e2dc7365bca9f9dbdd",
            "subj_verb_gender_attractor": "adeb87724b19d5be13e4ec68d9d279e20a76e1a7d3d54e556d85a21ddf8bcd87",
            "subj_verb_gender_csubj": "eb8a4144ad469e9a6c79672473a90893646ee2dc4b180b68f4aec0f3df6447cb",
            "subj_verb_gender_genitive": "6819172ae67b0db99c697e3c0af2d08a787db5b88829bcd4878b6272fa97d4d8",
            "subj_verb_gender_numerals": "8b94c9bdac228230d41ec471199adf9057ccd4a15c0edcd0768b529722794a0a",
            "subj_verb_gender_simple": "14334b6f3e4c1117ecf11259ee7282abf6545b108ee57deedb7ab35f4cfe807f",
            "subj_verb_number_csubj": "19b51a84c28f9f96005a04b01f579ef442777b7ffa3aeb19a07d91cf78555eab",
            "subj_verb_number_genitive": "fc73cb03b50ce385dd88fbbbf29de52ce602e4778163c6cc9a1d18349dac657b",
            "subj_verb_number_numerals": "47ddacaecb67ab1768a84e1434d494b0fce84026a2f04be3f2f6ed36698fe94f",
            "subj_verb_number_simple": "4082d81f56c872208580246d6189327302629f73c68dbe8ca2da147295016863",
            "subj_verb_person_csubj": "25d54713b0fcf53b0f311dc3a50ed7d1a10bec073133738e2f9832bd11906a8c",
            "subj_verb_person_genitive": "a6aa58460d49b4bbada3f94300d8d7dc5b5d898ecd490727b648b10feb0e9626",
            "subj_verb_person_numerals": "7d55ab9ea6eeefd67bc90207c12f995645ffde957ea23c667e1c95c70dfecdad",
            "subj_verb_person_simple": "69d5905c13c525869d6eede4db2052085bfde83aae0d0e4a3669a8716695a53b",
        },
        "pdb": {
            "subj_adjectival_case": "3c5199fda24205831fb4202ab9d41036e267a1225f58826baaf9b825c4dd019b",
            "subj_adjectival_gender": "1852238c7469cf080bd775f27accff2479c0c1ffd612914e7c31b791b74403dd",
            "subj_adjectival_gender_cop": "15b941350be1643a8214024d77610766ab46b949f452ac2a22658dc181052d85",
            "subj_adjectival_number": "9e00313bf8e1cfe9ff69318d517dcc58faca1c4194b1d1d4154cdd0e9b937965",
            "subj_adjectival_number_cop": "b954fe3fe768671f06bbec1902baaaad39565779738a838eb5209cec2af8a14d",
            "subj_verb_gender_attractor": "9e15d1df461330868bd6cde7e530669815572054935e2fa16bb311e518fc2277",
            "subj_verb_gender_csubj": "35d45ae16fdd209ca36732fe5e9a53a2575751520c9e482ed913e0f9f8065a87",
            "subj_verb_gender_genitive": "58b76cbb1e09078162062c474b6280c4e7e7af98578f3772452e744311da3a4c",
            "subj_verb_gender_numerals": "bf307bf82c2f5966581330c1558345ddf59aed88807ca6d081afadc3e9af5f8c",
            "subj_verb_gender_simple": "a372e2cc2e2e8972f5ad3a4e85e1da8c1272d0c321a98bb0b9a295fd6c4a7721",
            "subj_verb_number_csubj": "a45fb8bfad80173c16ebf7ccd2612cd3db3cfc125d7249fa232780a8e38cdae7",
            "subj_verb_number_genitive": "b2d294e7c7cd5f243cabc5fdae9bc4f6c1786c520cc4047a4fce181bf310f60e",
            "subj_verb_number_numerals": "656fa4ee3686a436becbf526e5b86efe8b49e903981f1252692a96abc783e565",
            "subj_verb_number_simple": "4ae711acfbb95ec06bc1d5891bbf7cd6d96b3b5697ea39406e7464ed85cbac26",
            "subj_verb_person_csubj": "74fb7f2e647e651c6ca5aa358d5fd2f7d344fbd05807eee710a9caf238745cd6",
            "subj_verb_person_genitive": "3eead87569fade9ae12bfca3f80ca2692559c6c0e531b6f821536d6d5dfe6853",
            "subj_verb_person_numerals": "29d74f80e636bc99c75380d52c859d5de423b985169f66469bbd0bfecdc7db92",
            "subj_verb_person_simple": "f7ce1b0323b3be4f274ba696353f3e8a26ce2bdb5d25bba22aa8ff298ee05725",
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
