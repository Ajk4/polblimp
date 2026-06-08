from __future__ import annotations

import unittest
from pathlib import Path

import conllu

from phenomena.common import sentence_text


class TestSentenceText(unittest.TestCase):
    def test_multiword_token_components_do_not_get_spaces(self) -> None:
        sentence = self._load_sentence("pl_pdb-ud-train.conllu", "train-s7190")

        self.assertEqual(
            "Ja nie byłem zbyt głodny, więc poprzestałem na sałatce.",
            sentence_text(sentence),
        )

        self._token_by_id(sentence, 3)["form"] = "byli"
        self._token_by_id(sentence, 4)["form"] = "śmy"
        self._token_by_id(sentence, 9)["form"] = "poprzestał"
        self._token_by_id(sentence, 10)["form"] = "em"

        self.assertEqual(
            "Ja nie byliśmy zbyt głodny, więc poprzestałem na sałatce.",
            sentence_text(sentence),
        )

    @staticmethod
    def _load_sentence(filename: str, sent_id: str) -> conllu.TokenList:
        path = Path(__file__).resolve().parents[1] / "data" / filename
        with path.open("r", encoding="utf-8") as handle:
            for sentence in conllu.parse_incr(handle):
                if sentence.metadata.get("sent_id") == sent_id:
                    return sentence

        raise AssertionError(f"Missing test sentence: {filename}:{sent_id}")

    @staticmethod
    def _token_by_id(sentence: conllu.TokenList, token_id: int) -> conllu.Token:
        for token in sentence:
            if token["id"] == token_id:
                return token

        raise AssertionError(f"Missing token id: {token_id}")
