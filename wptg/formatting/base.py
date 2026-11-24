from __future__ import annotations
from typing import Protocol
from wptg.models.graph import Graph


class IGraphTableFormatter(Protocol):
    def format_connections(self, graph: Graph) -> str:
        ...

    def format_adjacency_matrix(self, graph: Graph) -> str:
        ...

    def format_edges(self, graph: Graph) -> str:
        ...

    def format_html(self, graph: Graph, mode: str = "connections") -> str:
        ...
