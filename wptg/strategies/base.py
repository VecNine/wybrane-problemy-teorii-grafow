from __future__ import annotations
from typing import Protocol, List, Dict


class ISelectionStrategy(Protocol):
    def select(self, matches: List[Dict[int, int]]) -> List[Dict[int, int]]:
        ...
