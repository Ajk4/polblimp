from __future__ import annotations

import unittest
from collections.abc import Callable
from pathlib import Path

import conllu

from phenomena.common import load_sentences
from phenomena.subject_predicate_agreement.adjective.adjective_and_copula.subj_adjectival_gender_cop.generator import (
    match_subj_adjectival_gender_cop,
)
from phenomena.subject_predicate_agreement.adjective.adjective_and_copula.subj_adjectival_number_cop.generator import (
    match_subj_adjectival_number_cop,
)
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_case.generator import (
    match_subj_adjectival_case,
)
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_gender.generator import (
    match_subj_adjectival_gender,
)
from phenomena.subject_predicate_agreement.adjective.adjective_only.subj_adjectival_number.generator import (
    match_subj_adjectival_number,
)
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_simple.generator import (
    match_subj_verb_gender_simple_1a,
    match_subj_verb_gender_simple_1b,
    match_subj_verb_gender_simple_1c,
    match_subj_verb_gender_simple_2a,
    match_subj_verb_gender_simple_2b,
    match_subj_verb_gender_simple_2c,
)
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_numerals.generator import (
    match_subj_verb_gender_numerals_1a,
    match_subj_verb_gender_numerals_2a,
)
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_csubj.generator import (
    match_subj_verb_gender_csubj_1a,
    match_subj_verb_gender_csubj_2a,
)
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_genitive.generator import (
    match_subj_verb_gender_genitive_1a,
)
from phenomena.subject_predicate_agreement.verb.gender.subj_verb_gender_attractor.generator import (
    match_subj_verb_gender_attractor_1a,
    match_subj_verb_gender_attractor_1b,
    match_subj_verb_gender_attractor_1c,
    match_subj_verb_gender_attractor_2a,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_simple.generator import (
    match_subj_verb_number_simple_1a,
    match_subj_verb_number_simple_1b,
    match_subj_verb_number_simple_2a,
    match_subj_verb_number_simple_2b,
    match_subj_verb_number_simple_3a,
    match_subj_verb_number_simple_3b,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_csubj.generator import (
    match_subj_verb_number_csubj_1a,
    match_subj_verb_number_csubj_2a,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_genitive.generator import (
    match_subj_verb_number_genitive_1a,
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_numerals.generator import (
    match_subj_verb_number_numerals_1a,
    match_subj_verb_number_numerals_1b,
    match_subj_verb_number_numerals_1c,
    match_subj_verb_number_numerals_2a,
    match_subj_verb_number_numerals_2b,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    match_subj_verb_person_csubj_1a,
    match_subj_verb_person_csubj_2a,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_genitive.generator import (
    match_subj_verb_person_genitive_1a,
    match_subj_verb_person_genitive_1b,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_numerals.generator import (
    match_subj_verb_person_numerals_1a,
    match_subj_verb_person_numerals_1b,
    match_subj_verb_person_numerals_1c,
    match_subj_verb_person_numerals_2a,
    match_subj_verb_person_numerals_2b,
)


MatchFunction = Callable[[conllu.TokenList], object | None]
ExpectedCount = int | MatchFunction | None


class TestDatasetResultCounts(unittest.TestCase):

    """
    Numbers are from:
    * https://lindat.mff.cuni.cz/services/pmltq/?query=pdb#!/treebank/udpl_lfg218/query/CoeQIiQ/result?filter=true&timeout=30&limit=10000
    * https://lindat.mff.cuni.cz/services/pmltq/?query=pdb#!/treebank/udpl_pdb218/query/CoeQIiQ/result?filter=true&timeout=30&limit=10000
    """

    EXPECTED_RESULTS: dict[str, dict[MatchFunction, ExpectedCount]] = {
        "lfg": {
            match_subj_adjectival_case: match_subj_adjectival_number_cop,
            match_subj_adjectival_gender: 503,
            match_subj_adjectival_number: match_subj_adjectival_number_cop,
            match_subj_adjectival_gender_cop: 230,
            match_subj_adjectival_number_cop: 520,
            ##
            match_subj_verb_gender_simple_1a: 1627,
            match_subj_verb_gender_simple_1b: 264,
            match_subj_verb_gender_simple_1c: 373,
            match_subj_verb_gender_simple_2a: 352,
            match_subj_verb_gender_simple_2b: 23,
            match_subj_verb_gender_simple_2c: 62,
            match_subj_verb_gender_genitive_1a: 24,
            match_subj_verb_gender_csubj_1a: 40,
            match_subj_verb_gender_csubj_2a: 0,
            match_subj_verb_gender_numerals_1a: 139,
            match_subj_verb_gender_numerals_2a: 13,
            match_subj_verb_gender_attractor_1a: 51,
            match_subj_verb_gender_attractor_1b: 13,
            match_subj_verb_gender_attractor_1c: 9,
            match_subj_verb_gender_attractor_2a: 4,
            ##
            match_subj_verb_number_simple_1a: 6267,
            match_subj_verb_number_simple_1b: 217,
            match_subj_verb_number_simple_2a: 32,
            match_subj_verb_number_simple_2b: 37,
            match_subj_verb_number_simple_3a: 1021,
            match_subj_verb_number_simple_3b: 4,
            match_subj_verb_number_genitive_1a: 78,
            match_subj_verb_number_csubj_1a: match_subj_verb_person_csubj_1a,
            match_subj_verb_number_csubj_2a: match_subj_verb_person_csubj_2a,
            match_subj_verb_number_numerals_1a: match_subj_verb_person_numerals_1a,
            match_subj_verb_number_numerals_1b: match_subj_verb_person_numerals_1b,
            match_subj_verb_number_numerals_1c: match_subj_verb_person_numerals_1c,
            match_subj_verb_number_numerals_2a: match_subj_verb_person_numerals_2a,
            match_subj_verb_number_numerals_2b: match_subj_verb_person_numerals_2b,
            ##
            match_subj_verb_person_csubj_1a: 93,
            match_subj_verb_person_csubj_2a: 6,
            ##
            match_subj_verb_person_numerals_1a: 69,
            match_subj_verb_person_numerals_1b: 137,
            match_subj_verb_person_numerals_1c: 3,
            match_subj_verb_person_numerals_2a: 12,
            match_subj_verb_person_numerals_2b: 13 - 1, # IN connlu one matched sentence is duplicated
            ##
            match_subj_verb_person_genitive_1a: 54,
            match_subj_verb_person_genitive_1b: 24,
        },
        "pdb": {
            match_subj_adjectival_case: match_subj_adjectival_number_cop,
            match_subj_adjectival_gender: 1111,
            match_subj_adjectival_number: match_subj_adjectival_number_cop,
            match_subj_adjectival_gender_cop: 342,
            match_subj_adjectival_number_cop: 1125,
            ##
            match_subj_verb_gender_simple_2a: 525,
            match_subj_verb_gender_simple_2b: 29,
            match_subj_verb_gender_simple_2c: 126,
            match_subj_verb_gender_genitive_1a: 37,
            match_subj_verb_gender_csubj_1a: 32,
            match_subj_verb_gender_csubj_2a: 4,
            match_subj_verb_gender_numerals_1a: 141,
            match_subj_verb_gender_numerals_2a: 5,
            match_subj_verb_gender_attractor_1a: 88,
            match_subj_verb_gender_attractor_1b: 32,
            match_subj_verb_gender_attractor_1c: 2,
            match_subj_verb_gender_attractor_2a: 23,
        },
    }

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

    @classmethod
    def setUpClass(cls) -> None:
        cls.repo_root = Path(__file__).resolve().parents[1]
        cls.data_dir = cls.repo_root / "data"

        cls.sentences_by_dataset = {}
        for dataset_name, filenames in cls.DATASET_FILENAMES.items():
            paths = [cls.data_dir / filename for filename in filenames]
            for path in paths:
                if not path.exists():
                    raise FileNotFoundError(f"Missing {dataset_name} data file: {path}")

            sentences = []
            for path in paths:
                sentences.extend(load_sentences(path, skip_duplicates=False))
            cls.sentences_by_dataset[dataset_name] = sentences

    def test_expected_result_counts(self) -> None:
        for dataset_name, expected_counts in self.EXPECTED_RESULTS.items():
            self.assertIn(dataset_name, self.DATASET_FILENAMES)
            for match_fn, expected_count in expected_counts.items():
                with self.subTest(dataset=dataset_name, variant=match_fn.__name__):
                    if expected_count is None:
                        self.skipTest("TODO: fill expected count")
                    if not isinstance(expected_count, int):
                        expected_count = expected_counts[expected_count]
                    self.assertIsInstance(expected_count, int)

                    actual_count = sum(
                        1
                        for sentence in self.sentences_by_dataset[dataset_name]
                        if match_fn(sentence) is not None
                    )
                    self.assertEqual(expected_count, actual_count)
