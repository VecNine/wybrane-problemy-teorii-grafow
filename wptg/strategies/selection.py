from __future__ import annotations
from typing import List, Dict
from wptg.strategies.base import ISelectionStrategy


class AllAscendingStrategy:
    def select(self, matches: List[Dict[int, int]]) -> List[Dict[int, int]]:
        return sorted(matches, key=lambda m: min(m.values()))


class LowestIndexStrategy:
    def select(self, matches: List[Dict[int, int]]) -> List[Dict[int, int]]:
        if not matches:
            return []
        sorted_matches = sorted(matches, key=lambda m: min(m.values()))
        return [sorted_matches[0]]
