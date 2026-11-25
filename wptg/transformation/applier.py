from __future__ import annotations
from typing import Optional, Dict
from wptg.models.graph import Graph, Vertex, Edge
from wptg.models.production import Production
from wptg.models.enums import DanglingEdgesHandling
from wptg.transformation.base import IProductionApplier, IDanglingEdgesHandler
from wptg.transformation.dangling import DanglingEdgesHandler


class ProductionApplier:
    def __init__(self, dangling_handler: Optional[IDanglingEdgesHandler] = None):
        self.dangling_handler = dangling_handler or DanglingEdgesHandler()

    def apply(
        self,
        graph: Graph,
        production: Production,
        match: Dict[int, int],
        dangling_strategy: DanglingEdgesHandling
    ) -> Optional[Graph]:
        new_graph = graph.copy()

        mapping_dict = {m.left: m.right for m in production.mapping}
        retained_left = set(mapping_dict.keys())
        all_left = {v.index for v in production.left.vertices}
        deleted_left = all_left - retained_left

        deleted_g_indices = {match[l_idx] for l_idx in deleted_left}
        matched_g_indices = set(match.values())

        right_to_g: Dict[int, int] = {}
        for l_idx, r_idx in mapping_dict.items():
            g_idx = match[l_idx]
            right_to_g[r_idx] = g_idx
            r_vertex = production.right.get_vertex(r_idx)
            g_vertex = new_graph.get_vertex(g_idx)
            if r_vertex and g_vertex:
                g_vertex.label = r_vertex.label

        next_idx = new_graph.get_next_free_index()
        for r_v in production.right.vertices:
            if r_v.index not in right_to_g:
                right_to_g[r_v.index] = next_idx
                new_graph.vertices.append(Vertex(index=next_idx, label=r_v.label, x=r_v.x, y=r_v.y))
                next_idx += 1

        success, reconnected_edges = self.dangling_handler.resolve(
            graph,
            match,
            deleted_g_indices,
            matched_g_indices,
            production.embedding,
            right_to_g,
            dangling_strategy
        )

        if not success:
            return None

        left_edge_pairs = set()
        for pe in production.left.edges:
            gu, gv = match[pe.u], match[pe.v]
            key = (gu, gv) if new_graph.directed else (min(gu, gv), max(gu, gv))
            left_edge_pairs.add(key)

        filtered_edges = []
        for e in new_graph.edges:
            if e.u in deleted_g_indices or e.v in deleted_g_indices:
                continue
            edge_key = (e.u, e.v) if new_graph.directed else (min(e.u, e.v), max(e.u, e.v))
            if edge_key in left_edge_pairs:
                continue
            filtered_edges.append(e)

        new_graph.edges = filtered_edges

        for r_edge in production.right.edges:
            gu = right_to_g[r_edge.u]
            gv = right_to_g[r_edge.v]
            new_graph.edges.append(Edge(u=gu, v=gv, label=r_edge.label, weight=r_edge.weight))

        existing_keys = {
            (e.u, e.v) if new_graph.directed else (min(e.u, e.v), max(e.u, e.v))
            for e in new_graph.edges
        }
        for edge in reconnected_edges:
            key = (edge.u, edge.v) if new_graph.directed else (min(edge.u, edge.v), max(edge.u, edge.v))
            if key not in existing_keys:
                existing_keys.add(key)
                new_graph.edges.append(edge)

        new_graph.vertices = [v for v in new_graph.vertices if v.index not in deleted_g_indices]

        return new_graph
