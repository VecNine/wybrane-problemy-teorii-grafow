from __future__ import annotations
from typing import Tuple, List, Dict, Set
from wptg.models.graph import Graph, Edge
from wptg.models.production import EmbeddingRule
from wptg.models.enums import DanglingEdgesHandling
from wptg.transformation.base import IDanglingEdgesHandler


class DanglingEdgesHandler:
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
        g_to_left = {g_idx: l_idx for l_idx, g_idx in match.items()}

        for del_idx in deleted_g_indices:
            l_idx = g_to_left[del_idx]
            incident_edges = []
            for e in graph.edges:
                if e.u == del_idx or e.v == del_idx:
                    incident_edges.append(e)

            for e in incident_edges:
                is_u = (e.u == del_idx)
                neighbor_idx = e.v if is_u else e.u
                if neighbor_idx in matched_g_indices:
                    continue

                neighbor_v = graph.get_vertex(neighbor_idx)
                if neighbor_v is None:
                    continue

                matched_rules = []
                for rule in embedding_rules:
                    if rule.left_vertex == l_idx:
                        if rule.neighbor_label == "*" or rule.neighbor_label == neighbor_v.label:
                            matched_rules.append(rule)

                if not matched_rules:
                    if strategy == DanglingEdgesHandling.CANCEL:
                        return False, []
                    continue

                for rule in matched_rules:
                    for target_r in rule.connect_to:
                        if target_r in right_to_g_index:
                            target_g = right_to_g_index[target_r]
                            if graph.directed:
                                new_u = target_g if is_u else neighbor_idx
                                new_v = neighbor_idx if is_u else target_g
                                new_edges.append(Edge(u=new_u, v=new_v, label=e.label, weight=e.weight))
                            else:
                                new_edges.append(Edge(u=neighbor_idx, v=target_g, label=e.label, weight=e.weight))

        return True, new_edges
