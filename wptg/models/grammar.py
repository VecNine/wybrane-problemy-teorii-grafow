from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List
from wptg.models.graph import Graph
from wptg.models.production import Production
from wptg.models.enums import DanglingEdges


@dataclass
class Grammar:
    name: str
    start_graph: Graph
    productions: List[Production]
    nonterminals: List[str]
    terminals: List[str]
    directed: bool = False
    dangling_edges: DanglingEdges = DanglingEdges.FORBID

    @classmethod
    def from_dict(cls, data: dict) -> Grammar:
        g = data.get("grammar", data)
        labels = g.get("labels", {})
        return cls(
            name=g["name"],
            directed=g.get("directed", False),
            dangling_edges=DanglingEdges(g.get("danglingEdges", "forbid")),
            nonterminals=labels.get("nonterminals", []),
            terminals=labels.get("terminals", []),
            start_graph=Graph.from_dict(g["startGraph"]),
            productions=[Production.from_dict(p) for p in g.get("productions", [])]
        )

    def get_production(self, name: str) -> Optional[Production]:
        for p in self.productions:
            if p.name == name:
                return p
        return None
