from __future__ import annotations

import unittest
from pathlib import Path

import conllu

from phenomena.common import load_sentences
from phenomena.morph_dictionary import MorphDictionary
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_simple.generator import (
    run_subj_verb_gender_simple,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_simple.generator import (
    run_subj_verb_number_simple,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    run_subj_verb_person_csubj,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_genitive.generator import (
    run_subj_verb_person_genitive,
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
                "dataset": ("pl_lfg-ud-train.conllu", 176),
                "source": "A pan ma?",
                "transform": run_subj_verb_person_simple,
                "expected": "A pan masz?",
            },
            {
                "dataset": ("pl_lfg-ud-train.conllu", 892),
                "source": "Bożena też nie ma z czego zwrócić pożyczki.",
                "transform": run_subj_verb_person_simple,
                "expected": "Bożena też nie masz z czego zwrócić pożyczki.",
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
            {
                "dataset": ("pl_pdb-ud-train.conllu", 5673),
                "source": "W kratkach z cyframi skarbów nie ma.",
                "transform": run_subj_verb_person_genitive,
                "expected": "W kratkach z cyframi skarbów nie jestem.",
            },
            {
                "dataset": ("pl_pdb-ud-train.conllu", 13969),
                "source": (
                    "Wracając jednak do zaburzenia rytmu domowego, którego nastolatki nie zauważyły, "
                    "połowa przepytanych nastolatków przyznała też, że regularnie budzi się w nocy, "
                    "żeby zaktualizować statusy, wrzucić zdjęcia, dać jakieś lajki albo sprawdzić, "
                    "ile ma się własnych lajków."
                ),
                "transform": run_subj_verb_gender_simple,
                "expected": (
                    "Wracając jednak do zaburzenia rytmu domowego, którego nastolatki nie zauważyli, "
                    "połowa przepytanych nastolatków przyznała też, że regularnie budzi się w nocy, "
                    "żeby zaktualizować statusy, wrzucić zdjęcia, dać jakieś lajki albo sprawdzić, "
                    "ile ma się własnych lajków."
                ),
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
        return load_sentences(self.repo_root / "data" / filename, skip_duplicates=False)[index]
