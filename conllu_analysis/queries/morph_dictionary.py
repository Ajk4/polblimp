from __future__ import annotations

import csv
from dataclasses import dataclass
from itertools import zip_longest
from pathlib import Path
from typing import Optional


def is_subtag(tag: str, supertag: str) -> bool:
    if tag == supertag:
        return True

    tag_parts = tag.split(":")
    supertag_parts = supertag.split(":")

    for tag_part, supertag_part in zip_longest(tag_parts, supertag_parts):
        if supertag_part is None:
            # so praet:pl:m3:imperf:nagl matches praet:pl:m3:imperf
            return tag_part == "nagl"
        supertag_part_options = supertag_part.split(".")

        if "_" in supertag_part_options:
            return True

        if tag_part is None:
            # so praet:sg:m1:imperf matches praet:sg:m1.m2.m3:imperf:nagl
            return "nagl" in supertag_part_options
        if tag_part not in supertag_part_options:
            return False
    return True


@dataclass(frozen=True)
class MorphDictionary:
    _entries: dict[str, tuple[tuple[str, str], ...]]

    @classmethod
    def load(cls, morph_dict_path: Path) -> "MorphDictionary":
        with morph_dict_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None or "lemma" not in reader.fieldnames:
                raise ValueError(f"Missing 'lemma' column in morphology CSV: {morph_dict_path}")

            entries: dict[str, tuple[tuple[str, str], ...]] = {}
            for row in reader:
                lemma = row.get("lemma")
                if not lemma:
                    continue

                forms = tuple(
                    (tag, form)
                    for tag, form in row.items()
                    if tag != "lemma" and form
                )
                entries[lemma] = forms

        return cls(entries)

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, lemma: str) -> bool:
        return self.has_lemma(lemma)

    def has_lemma(self, lemma: str) -> bool:
        return lemma in self._entries

    def get_form(self, lemma: str, tag: str) -> Optional[str]:
        forms = self._entries.get(lemma)
        if forms is None:
            return None

        normalized_tag = self._normalize_tag(tag)
        for candidate_tag, form in forms:
            if is_subtag(normalized_tag, candidate_tag):
                return form

        return None

    @staticmethod
    def _normalize_tag(tag: str) -> str:
        # Keep compatibility with legacy neuter/masculine lookup shortcuts.
        if ":n:" in tag:
            tag = tag.replace(":n:", ":n1:")
        if ":m:" in tag:
            tag = tag.replace(":m:", ":m1:")
        return tag
