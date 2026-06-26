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
            "subj_verb_gender_csubj": "b4973ed8d329f895159d487757b1c387d2a585469215d2455b77b44ce0608c08",
            "subj_verb_gender_genitive": "e1f95054ae695715fd633e70e66a3c4a7fb51d7d5e19ec6c38bd5f9600e18b02",
            "subj_verb_gender_numerals": "8b94c9bdac228230d41ec471199adf9057ccd4a15c0edcd0768b529722794a0a",
            "subj_verb_gender_simple": "f0abdf588fbd9779017860fff09d5b5d8ba4365a6659a83ecb1ed03031206b2c",
            "subj_verb_number_csubj": "c22c8758a64e49732f9b00f1f7c747a28532d9403891946b6c245d9b16585675",
            "subj_verb_number_genitive": "fc73cb03b50ce385dd88fbbbf29de52ce602e4778163c6cc9a1d18349dac657b",
            "subj_verb_number_numerals": "2ea33c835b593109238d260c3fb2657f23b5203726edcd3e3f898693b2217c4b",
            "subj_verb_number_simple": "4082d81f56c872208580246d6189327302629f73c68dbe8ca2da147295016863",
            "subj_verb_person_csubj": "55e5ed22d4672f3fa4bf867e15f16deaa35bf3c75b63aee05e0c8e13c9a6c4ec",
            "subj_verb_person_genitive": "a6aa58460d49b4bbada3f94300d8d7dc5b5d898ecd490727b648b10feb0e9626",
            "subj_verb_person_numerals": "2f5af06ee042f67e235b8ee266f760843358d5995662339ce2e9bdeb500b1243",
            "subj_verb_person_simple": "69d5905c13c525869d6eede4db2052085bfde83aae0d0e4a3669a8716695a53b",
        },
        "pdb": {
            "subj_adjectival_case": "3c5199fda24205831fb4202ab9d41036e267a1225f58826baaf9b825c4dd019b",
            "subj_adjectival_gender": "1852238c7469cf080bd775f27accff2479c0c1ffd612914e7c31b791b74403dd",
            "subj_adjectival_gender_cop": "15b941350be1643a8214024d77610766ab46b949f452ac2a22658dc181052d85",
            "subj_adjectival_number": "9e00313bf8e1cfe9ff69318d517dcc58faca1c4194b1d1d4154cdd0e9b937965",
            "subj_adjectival_number_cop": "b954fe3fe768671f06bbec1902baaaad39565779738a838eb5209cec2af8a14d",
            "subj_verb_gender_csubj": "c0af288c18dc4cf9dd9fb85cb1e5d590570e34ca52dc5f9e51da1290b6d7930f",
            "subj_verb_gender_genitive": "b3ebb3633dd950eb7e8a91d25bde8583785f87e7c7f36a5b92abab1256c400b6",
            "subj_verb_gender_numerals": "bf307bf82c2f5966581330c1558345ddf59aed88807ca6d081afadc3e9af5f8c",
            "subj_verb_gender_simple": "adc18b4c937b9d1c2289bcf934ae2d325434ed72c20c3440bb5fa72430752045",
            "subj_verb_number_csubj": "eb6f7c3744d595eb325775916cc4ebed664fd67a9fca5f190c476885ad1f3243",
            "subj_verb_number_genitive": "b2d294e7c7cd5f243cabc5fdae9bc4f6c1786c520cc4047a4fce181bf310f60e",
            "subj_verb_number_numerals": "13c32a7c28a61fc4c673f32b6c814122c0de5c0ce485a6eb4ed0b87ceb9fea23",
            "subj_verb_number_simple": "4ae711acfbb95ec06bc1d5891bbf7cd6d96b3b5697ea39406e7464ed85cbac26",
            "subj_verb_person_csubj": "83cd765a00880f1f0abfb4ebf840b336d05ecab388e2745c7717096fd5a2e8e6",
            "subj_verb_person_genitive": "3eead87569fade9ae12bfca3f80ca2692559c6c0e531b6f821536d6d5dfe6853",
            "subj_verb_person_numerals": "35cf244c459cf68fe303deda349941ee4e3ca2cfe98776bfa4b150ae8d83793e",
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
