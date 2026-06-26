from __future__ import annotations

import unittest
from pathlib import Path

import conllu

from phenomena.common import load_sentences
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_simple.generator import (
    run_subj_verb_number_simple,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    run_subj_verb_person_csubj,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_simple.generator import (
    run_subj_verb_person_simple,
)


class TestSentenceText(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.morph_dict = MorphDictionary.load(cls.repo_root / "dictionary.v4.csv")

    def test_generated_sentence_outputs(self) -> None:
        cases = [
            {
                "dataset": ("pl_lfg-ud-test.conllu", 1574),
                "source": "Wydawało mi się, że prowadzę z drzewem bezgłośny dialog.",
                "transform": run_subj_verb_person_csubj,
                "expected": "Wydawałoś mi się, że prowadzę z drzewem bezgłośny dialog.",
            },
            {
                "dataset": ("pl_lfg-ud-test.conllu", 1575),
                "source": "Wydawało się, że jej życie dobiegnie końca bez większych niespodzianek.",
                "transform": run_subj_verb_person_csubj,
                "expected": "Wydawałoś się, że jej życie dobiegnie końca bez większych niespodzianek.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 3082),
                "source": "I to była prawda.",
                "transform": run_subj_verb_person_simple,
                "expected": "I to byłam prawda.",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 3083),
                "source": "i to byłby komplet..",
                "transform": run_subj_verb_person_simple,
                "expected": "i to byłbyś komplet..",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 7189),
                "source": "Ja nie byłem zbyt głodny, więc poprzestałem na sałatce.",
                "transform": run_subj_verb_number_simple,
                "expected": "Ja nie byliśmy zbyt głodny, więc poprzestałem na sałatce.",
            },
        ]

        for case in cases:
            with self.subTest(expected=case["expected"]):
                sentence = self._get_sentence(case)
                self.assertEqual(case["source"], sentence.metadata["text"])
                transform = case["transform"]
                df = transform([sentence], self.morph_dict, None)

                self.assertEqual(1, len(df))
                self.assertEqual(case["expected"], df.iloc[0]["incorrect"])

    def _get_sentence(self, case: dict) -> conllu.TokenList:
        filename, index = case["dataset"]
        return load_sentences(self.repo_root / "data" / filename)[index]
