from __future__ import annotations

import json
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
    match_subj_verb_gender_attractor_2b,
    match_subj_verb_gender_attractor_2c,
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
)
from phenomena.subject_predicate_agreement.verb.number.subj_verb_number_attractor.generator import (
    match_subj_verb_number_attractor_1a,
    match_subj_verb_number_attractor_1b,
    match_subj_verb_number_attractor_1c,
    match_subj_verb_number_attractor_2a,
    match_subj_verb_number_attractor_2b,
    match_subj_verb_number_attractor_3a,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_csubj.generator import (
    match_subj_verb_person_csubj_1a,
    match_subj_verb_person_csubj_2a,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_genitive.generator import (
    match_subj_verb_person_genitive_1a,
    match_subj_verb_person_genitive_1b,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_simple.generator import (
    match_subj_verb_person_simple_1a,
    match_subj_verb_person_simple_1b,
    match_subj_verb_person_simple_1c,
    match_subj_verb_person_simple_1d,
    match_subj_verb_person_simple_2a,
    match_subj_verb_person_simple_2b,
    match_subj_verb_person_simple_2c,
)
from phenomena.subject_predicate_agreement.verb.person.subj_verb_person_numerals.generator import (
    match_subj_verb_person_numerals_1a,
    match_subj_verb_person_numerals_1b,
    match_subj_verb_person_numerals_1c,
    match_subj_verb_person_numerals_2a,
    match_subj_verb_person_numerals_2b,
)


MatchFunction = Callable[[conllu.TokenList], object | None]
ExpectedCount = int | str | None
ExpectedCounts = ExpectedCount | list[ExpectedCount]
MATCHERS = {
    matcher.__name__: matcher
    for matcher in (
        match_subj_adjectival_case,
        match_subj_adjectival_gender,
        match_subj_adjectival_number,
        match_subj_adjectival_gender_cop,
        match_subj_adjectival_number_cop,
        match_subj_verb_gender_simple_1a,
        match_subj_verb_gender_simple_1b,
        match_subj_verb_gender_simple_1c,
        match_subj_verb_gender_simple_2a,
        match_subj_verb_gender_simple_2b,
        match_subj_verb_gender_simple_2c,
        match_subj_verb_gender_genitive_1a,
        match_subj_verb_gender_csubj_1a,
        match_subj_verb_gender_csubj_2a,
        match_subj_verb_gender_numerals_1a,
        match_subj_verb_gender_numerals_2a,
        match_subj_verb_gender_attractor_1a,
        match_subj_verb_gender_attractor_1b,
        match_subj_verb_gender_attractor_1c,
        match_subj_verb_gender_attractor_2a,
        match_subj_verb_gender_attractor_2b,
        match_subj_verb_gender_attractor_2c,
        match_subj_verb_number_simple_1a,
        match_subj_verb_number_simple_1b,
        match_subj_verb_number_simple_1c,
        match_subj_verb_number_simple_2a,
        match_subj_verb_number_simple_2b,
        match_subj_verb_number_simple_3a,
        match_subj_verb_number_simple_3b,
        match_subj_verb_number_genitive_1a,
        match_subj_verb_number_csubj_1a,
        match_subj_verb_number_csubj_2a,
        match_subj_verb_number_attractor_1a,
        match_subj_verb_number_attractor_1b,
        match_subj_verb_number_attractor_1c,
        match_subj_verb_number_attractor_2a,
        match_subj_verb_number_attractor_2b,
        match_subj_verb_number_attractor_3a,
        match_subj_verb_number_numerals_1a,
        match_subj_verb_number_numerals_1b,
        match_subj_verb_number_numerals_1c,
        match_subj_verb_number_numerals_2a,
        match_subj_verb_person_csubj_1a,
        match_subj_verb_person_csubj_2a,
        match_subj_verb_person_simple_1a,
        match_subj_verb_person_simple_1b,
        match_subj_verb_person_simple_1c,
        match_subj_verb_person_simple_1d,
        match_subj_verb_person_simple_2a,
        match_subj_verb_person_simple_2b,
        match_subj_verb_person_simple_2c,
        match_subj_verb_person_numerals_1a,
        match_subj_verb_person_numerals_1b,
        match_subj_verb_person_numerals_1c,
        match_subj_verb_person_numerals_2a,
        match_subj_verb_person_numerals_2b,
        match_subj_verb_person_genitive_1a,
        match_subj_verb_person_genitive_1b,
    )
}


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

    EXPECTED_RESULTS: dict[str, ExpectedCounts] = json.loads(
        Path(__file__).with_name("dataset_result_counts.json").read_text()
    )

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
        self.assertEqual(set(self.EXPECTED_RESULTS), set(MATCHERS))
        for dataset_index, dataset_name in enumerate(self.DATASET_ORDER):
            self.assertIn(dataset_name, self.DATASET_FILENAMES)
            for match_name, expected_counts in self.EXPECTED_RESULTS.items():
                self.assertIn(match_name, MATCHERS, f"Unknown matcher in counts file: {match_name}")
                match_fn = MATCHERS[match_name]
                with self.subTest(dataset=dataset_name, variant=match_name):
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
