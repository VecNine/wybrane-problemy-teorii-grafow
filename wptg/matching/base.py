from __future__ import annotations
from typing import Protocol, List, Dict
from wptg.models.graph import Graph


class IGraphMatcher(Protocol):
    def find_matches(self, graph: Graph, pattern: Graph) -> List[Dict[int, int]]:
        ...
