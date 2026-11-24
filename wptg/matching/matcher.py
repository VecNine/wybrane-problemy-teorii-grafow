from __future__ import annotations
from typing import List, Dict, Set
from wptg.models.graph import Graph
from wptg.matching.base import IGraphMatcher


class GraphMatcher:
    def find_matches(self, graph: Graph, pattern: Graph) -> List[Dict[int, int]]:
        if not pattern.vertices:
            return []

        if len(pattern.vertices) == 1:
            p_vertex = pattern.vertices[0]
            matches = []
            for v in sorted(graph.vertices, key=lambda v: v.index):
                if v.label == p_vertex.label:
                    matches.append({p_vertex.index: v.index})
            return matches

        p_vertices = pattern.vertices
        matches = []
        n = len(p_vertices)

        def is_valid_partial(mapping: Dict[int, int]) -> bool:
            mapped_p = set(mapping.keys())
            for pe in pattern.edges:
                if pe.u in mapped_p and pe.v in mapped_p:
                    gu, gv = mapping[pe.u], mapping[pe.v]
                    edge_found = False
                    for ge in graph.edges:
                        if graph.directed:
                            if ge.u == gu and ge.v == gv:
                                edge_found = True
                                break
                        else:
                            if (ge.u == gu and ge.v == gv) or (ge.u == gv and ge.v == gu):
                                edge_found = True
                                break
                    if not edge_found:
                        return False
            return True

        def backtrack(depth: int, current: Dict[int, int], used: Set[int]):
            if depth == n:
                matches.append(dict(current))
                return

            p_v = p_vertices[depth]
            for g_v in sorted(graph.vertices, key=lambda v: v.index):
                if g_v.index in used:
                    continue
                if g_v.label != p_v.label:
                    continue

                current[p_v.index] = g_v.index
                used.add(g_v.index)

                if is_valid_partial(current):
                    backtrack(depth + 1, current, used)

                used.remove(g_v.index)
                del current[p_v.index]

        backtrack(0, {}, set())
        return matches
