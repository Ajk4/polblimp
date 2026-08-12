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
            "subj_adjectival_case": "5d69b76821ae3e45d41fd9cc479533cbcf5d84058ab0457fc9cccb16d5946bc7",
            "subj_adjectival_gender": "b20a342d599e55d2d0a913eee44c3e3e0a04dc4c8c4b9ec407e1e97618bad87e",
            "subj_adjectival_gender_cop": "32f6eb773e95667b8bd57ce7d13509ff35702c65c1dc5ef4e0a2b951bda73786",
            "subj_adjectival_number": "bbbef31f1847a4deee56b1e165515f6d0b5e45280d06087032e93a7a0b7e0132",
            "subj_adjectival_number_cop": "19ceccba49acff6886bd517d078581822f5adc83ec3087af7a8c0823728cb2fd",
            "subj_verb_gender_attractor": "bc8be509a24b14658e4c27e0e68b70e33e203df0965f0437651fc1f8ba77afc4",
            "subj_verb_gender_csubj": "eb8a4144ad469e9a6c79672473a90893646ee2dc4b180b68f4aec0f3df6447cb",
            "subj_verb_gender_genitive": "6819172ae67b0db99c697e3c0af2d08a787db5b88829bcd4878b6272fa97d4d8",
            "subj_verb_gender_numerals": "f68af2433d64106ca47c650fdfbcedaf6cb4de1e3e11866862e591a1bb71a5cc",
            "subj_verb_gender_simple": "c6dcebdfac22e7f7b23a6b4615179acf1ab88a331e0a20d5c89547f0018fa198",
            "subj_verb_number_csubj": "19b51a84c28f9f96005a04b01f579ef442777b7ffa3aeb19a07d91cf78555eab",
            "subj_verb_number_attractor": "55c23bc52becdcca66b3f0ec2e9895fd8010a8b27520bea63b2bcdb838eb3ffb",
            "subj_verb_number_genitive": "6f663d2e27fc0f96e35a66517d8e4569b833074b6ef03029cc0ecc9b4211db46",
            "subj_verb_number_numerals": "46437044e4de8ee4a4e0bf995daae81a8c34ed442cd68b32c15783b0a934df1f",
            "subj_verb_number_simple": "a939128b89d0c45484561dac77691044e852b4f59a3ea48a3d8a493d5dc07c35",
            "subj_verb_person_csubj": "25d54713b0fcf53b0f311dc3a50ed7d1a10bec073133738e2f9832bd11906a8c",
            "subj_verb_person_genitive": "c6d040f7e4553805e32ca5e5244b97bc788ae6f40bd0ffee85b2e75f2d80e842",
            "subj_verb_person_numerals": "7d55ab9ea6eeefd67bc90207c12f995645ffde957ea23c667e1c95c70dfecdad",
            "subj_verb_person_simple": "75f679640ecc117977c7e6dfaf939a48ca36b05e3898d8129c6b1453e7fd72bb",
        },
        "pdb": {
            "subj_adjectival_case": "0e27b5132d314456607386e6f0c82157d276c8467f54fed14a9324ae788e34db",
            "subj_adjectival_gender": "94d01f8fb8918ab2dc2881d0ea2d5ad7f7135a9b73068d289ed82d3dda9038df",
            "subj_adjectival_gender_cop": "b17bf0e54937134fa9746f897435aa67cfefc8fdb9688082edbfcd2e01ff6cd1",
            "subj_adjectival_number": "9d6e67acd11a4525f7c6ef74179e0639d61232f8941ea7a5d8c63b0225435676",
            "subj_adjectival_number_cop": "8247f93768ec97b1d4be2e8f31333ec272a6da6d2a3297a51c287befb40c865c",
            "subj_verb_gender_attractor": "6d4d1736f6508914c04bf3d1648560b9f52459af913b3b267e5ab8591d40618b",
            "subj_verb_gender_csubj": "35d45ae16fdd209ca36732fe5e9a53a2575751520c9e482ed913e0f9f8065a87",
            "subj_verb_gender_genitive": "bc8481a8b054ea85ec05a43458ca6390d7f426f42a3c5e3dc1b1a845241a8cfd",
            "subj_verb_gender_numerals": "45fa518d1d9ce70cc94cebf85874784517e606904653fd30f43516e1de32ee09",
            "subj_verb_gender_simple": "7f465f4d404150019da8c74a4183bd28ade51f3d2a7868cc7bde44325cb46ff1",
            "subj_verb_number_csubj": "a45fb8bfad80173c16ebf7ccd2612cd3db3cfc125d7249fa232780a8e38cdae7",
            "subj_verb_number_attractor": "5c44b8ab42548719514835436db4d78125cf147130566a60926b8a9dbc57f7ee",
            "subj_verb_number_genitive": "56e19bf4341319425532e0b8dc6c749d331ba57a8aa6087aff21942d537b1c89",
            "subj_verb_number_numerals": "cc3a09a6e3c514f4c82276c13566a8433f53f5eb2a875464c998f4ca9070e857",
            "subj_verb_number_simple": "fedc53d32ac3fad3f638e750bc8c0bdbf8e19b9b8da666e269c8eaf64ce55f26",
            "subj_verb_person_csubj": "cd6134c388eebabb8609303f58dbce2f00800e2770e4f57cc1ac00eb2f474f89",
            "subj_verb_person_genitive": "625bfebdcfd7da82f594858ee9473e2d3baf2cb0af2f4546ceec61363aa15053",
            "subj_verb_person_numerals": "52a021780b7bf08c366fea3fc50b8b4aff0ebc565355a4617daef242da14f899",
            "subj_verb_person_simple": "1f6d1429b30d48b83be47c686f91ad4a27ed627c629d86792ebf0f4a6c2d2eea",
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
