from __future__ import annotations
from typing import Tuple, List, Dict, Set
from wptg.models.graph import Graph, Edge
from wptg.models.production import EmbeddingRule
from wptg.models.enums import DanglingEdgesHandling
from wptg.transformation.base import IDanglingEdgesHandler


class DanglingEdgesHandler:
    def _build_edge(self, graph: Graph, neighbor_idx: int, target_g: int, is_u: bool, original: Edge) -> Edge:
        if graph.directed:
            new_u = target_g if is_u else neighbor_idx
            new_v = neighbor_idx if is_u else target_g
            return Edge(u=new_u, v=new_v, label=original.label, weight=original.weight)
        return Edge(u=neighbor_idx, v=target_g, label=original.label, weight=original.weight)

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
        new_edges: List[Edge] = []
        seen_pairs: Set[Tuple[int, int]] = set()
        g_to_left = {g_idx: l_idx for l_idx, g_idx in match.items()}

        for g_idx in matched_g_indices:
            l_idx = g_to_left[g_idx]
            is_deleted = g_idx in deleted_g_indices
            incident_edges = [e for e in graph.edges if e.u == g_idx or e.v == g_idx]

            for e in incident_edges:
                is_u = (e.u == g_idx)
                neighbor_idx = e.v if is_u else e.u
                if neighbor_idx in matched_g_indices:
                    continue

                neighbor_v = graph.get_vertex(neighbor_idx)
                if neighbor_v is None:
                    continue

                matched_rules = [
                    rule
                    for rule in embedding_rules
                    if rule.left_vertex == l_idx
                    and (rule.neighbor_label == "*" or rule.neighbor_label == neighbor_v.label)
                ]

                if is_deleted and not matched_rules:
                    if strategy == DanglingEdgesHandling.CANCEL:
                        return False, []
                    continue

                for rule in matched_rules:
                    for target_r in rule.connect_to:
                        if target_r not in right_to_g_index:
                            continue
                        target_g = right_to_g_index[target_r]
                        if not is_deleted and target_g == g_idx:
                            continue
                        new_edge = self._build_edge(graph, neighbor_idx, target_g, is_u, e)
                        key = (
                            (new_edge.u, new_edge.v)
                            if graph.directed
                            else (min(new_edge.u, new_edge.v), max(new_edge.u, new_edge.v))
                        )
                        if key not in seen_pairs:
                            seen_pairs.add(key)
                            new_edges.append(new_edge)

        return True, new_edges
