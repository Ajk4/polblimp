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
    match_subj_verb_number_simple_1c,
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
ExpectedCounts = ExpectedCount | list[ExpectedCount]


class TestDatasetResultCounts(unittest.TestCase):

    """
    Numbers are from:
    * https://lindat.mff.cuni.cz/services/pmltq/?query=pdb#!/treebank/udpl_lfg218/query/CoeQIiQ/result?filter=true&timeout=30&limit=10000
    * https://lindat.mff.cuni.cz/services/pmltq/?query=pdb#!/treebank/udpl_pdb218/query/CoeQIiQ/result?filter=true&timeout=30&limit=10000

    IMPORTANT - web search engine returns all possible matches.
    If sentence can be matched two different ways, both ways are returned. It might inflate some numbers in this test.
    For those cases test here points to multiple-matches-per-sentence aware matcher.

    In normal pair-generation mode we take only one match.
    """

    DATASET_ORDER = ("lfg", "pdb")

    EXPECTED_RESULTS: dict[MatchFunction, ExpectedCounts] = {
        match_subj_adjectival_case: match_subj_adjectival_number_cop,
        match_subj_adjectival_gender: [503, 1111],
        match_subj_adjectival_number: match_subj_adjectival_number_cop,
        match_subj_adjectival_gender_cop: [230, 342],
        match_subj_adjectival_number_cop: [520, 1125],
        ##
        match_subj_verb_gender_simple_1a: [1867, 2830],
        match_subj_verb_gender_simple_1b: [306, 485],
        match_subj_verb_gender_simple_1c: [438, 639],
        match_subj_verb_gender_simple_2a: [352, 528],
        match_subj_verb_gender_simple_2b: [23, 29],
        match_subj_verb_gender_simple_2c: [62, 126],
        match_subj_verb_gender_genitive_1a: [27, 69],
        match_subj_verb_gender_csubj_1a: [48, 48],
        match_subj_verb_gender_csubj_2a: [1, 9],
        match_subj_verb_gender_numerals_1a: [148, 195],
        match_subj_verb_gender_numerals_2a: [14, 9],
        match_subj_verb_gender_attractor_1a: [51, 88],
        match_subj_verb_gender_attractor_1b: [13, 32],
        match_subj_verb_gender_attractor_1c: [9, 2],
        match_subj_verb_gender_attractor_2a: [4, 23],
        ##
        match_subj_verb_number_simple_1a: [7240, None], # over 10k for pdb
        match_subj_verb_number_simple_1b: [241, 213],
        match_subj_verb_number_simple_1c: [99, 63],
        match_subj_verb_number_simple_2a: [35, 105],
        match_subj_verb_number_simple_2b: [45, 188],
        match_subj_verb_number_simple_3a: [1174, 2391],
        match_subj_verb_number_simple_3b: [4, 5],
        match_subj_verb_number_genitive_1a: [93, 214],
        match_subj_verb_number_csubj_1a: [105, 127],
        match_subj_verb_number_csubj_2a: [7, 32],
        ##
        match_subj_verb_number_numerals_1a: [227, 782],
        match_subj_verb_number_numerals_1b: [1, 4],
        match_subj_verb_number_numerals_1c: [2, 2],
        match_subj_verb_number_numerals_2a: [27, 23],
        ##
        match_subj_verb_person_csubj_1a: match_subj_verb_number_csubj_1a,
        match_subj_verb_person_csubj_2a: match_subj_verb_number_csubj_2a,
        ##
        match_subj_verb_person_numerals_1a: [79, 587],
        match_subj_verb_person_numerals_1b: [146, 193],
        match_subj_verb_person_numerals_1c: [3, 6],
        match_subj_verb_person_numerals_2a: [13, 11],
        match_subj_verb_person_numerals_2b: [14, 10],
        ##
        match_subj_verb_person_genitive_1a: [54, None],
        match_subj_verb_person_genitive_1b: [24, None],
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
        for dataset_index, dataset_name in enumerate(self.DATASET_ORDER):
            self.assertIn(dataset_name, self.DATASET_FILENAMES)
            for match_fn, expected_counts in self.EXPECTED_RESULTS.items():
                with self.subTest(dataset=dataset_name, variant=match_fn.__name__):
                    expected_count = self.expected_count_for_dataset(expected_counts, dataset_index)
                    if expected_count is None:
                        continue
                    if not isinstance(expected_count, int):
                        expected_count = self.expected_count_for_dataset(
                            self.EXPECTED_RESULTS[expected_count],
                            dataset_index,
                        )
                    self.assertIsInstance(expected_count, int)

                    actual_count = sum(
                        count_matches(match_fn(sentence))
                        for sentence in self.sentences_by_dataset[dataset_name]
                    )
                    self.assertEqual(expected_count, actual_count)

    def expected_count_for_dataset(
            self,
            expected_counts: ExpectedCounts,
            dataset_index: int,
    ) -> ExpectedCount:
        if isinstance(expected_counts, list):
            self.assertEqual(len(expected_counts), len(self.DATASET_ORDER))
            return expected_counts[dataset_index]
        return expected_counts


def count_matches(result: object | None) -> int:
    if isinstance(result, list):
        return len(result)
    if result is None:
        return 0
    return 1
