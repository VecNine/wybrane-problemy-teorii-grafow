from __future__ import annotations
from typing import Protocol, Optional, Tuple, List, Dict, Set
from wptg.models.graph import Graph, Edge
from wptg.models.production import EmbeddingRule, Production
from wptg.models.enums import DanglingEdgesHandling


class IDanglingEdgesHandler(Protocol):
    def resolve(
        self,
        graph: Graph,
        match: Dict[int, int],
        deleted_g_indices: Set[int],
        matched_g_indices: Set[int],
        embedding_rules: List[EmbeddingRule],
        right_to_g_index: Dict[int, int],
        strategy: DanglingEdgesHandling
    ) -> Tuple[bool, List[Edge]]:
        ...


class IProductionApplier(Protocol):
    def apply(
        self,
        graph: Graph,
        production: Production,
        match: Dict[int, int],
        dangling_strategy: DanglingEdgesHandling
    ) -> Optional[Graph]:
        ...
