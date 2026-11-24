from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List
from wptg.models.graph import Graph
from wptg.models.enums import DanglingEdges


@dataclass
class Mapping:
    left: int
    right: int


@dataclass
class EmbeddingRule:
    left_vertex: int
    neighbor_label: str
    connect_to: List[int]

    @classmethod
    def from_dict(cls, data: dict) -> EmbeddingRule:
        return cls(
            left_vertex=data["leftVertex"],
            neighbor_label=data["neighborLabel"],
            connect_to=list(data.get("connectTo", []))
        )


@dataclass
class Production:
    name: str
    left: Graph
    right: Graph
    mapping: List[Mapping] = field(default_factory=list)
    embedding: List[EmbeddingRule] = field(default_factory=list)
    directed: bool = False
    description: Optional[str] = None
    dangling_edges: Optional[DanglingEdges] = None

    @classmethod
    def from_dict(cls, data: dict) -> Production:
        p = data.get("production", data)
        dangling = p.get("danglingEdges")
        return cls(
            name=p["name"],
            directed=p.get("directed", False),
            description=p.get("description"),
            dangling_edges=DanglingEdges(dangling) if dangling else None,
            left=Graph.from_dict(p["left"]),
            right=Graph.from_dict(p["right"]),
            mapping=[Mapping(left=m["left"], right=m["right"]) for m in p.get("mapping", [])],
            embedding=[EmbeddingRule.from_dict(e) for e in p.get("embedding", [])]
        )

    def visualize(self, figsize: tuple = (11, 4.5)):
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

        retained_left = {m.left for m in self.mapping}
        colors_left = {
            v.index: "#bbf7d0" if v.index in retained_left else "#fecaca"
            for v in self.left.vertices
        }

        retained_right = {m.right for m in self.mapping}
        colors_right = {
            v.index: "#bbf7d0" if v.index in retained_right else "#fed7aa"
            for v in self.right.vertices
        }

        self.left.visualize(title=f"{self.name}: Lewa strona (Wzorzec)", ax=ax1, node_colors=colors_left)
        self.right.visualize(title=f"{self.name}: Prawa strona (Wynik)", ax=ax2, node_colors=colors_right)

        plt.suptitle(
            f"Produkcja {self.name}  [Zielony = zachowany, Czerwony = usuwany, Pomarańczowy = nowy]",
            fontsize=12,
            y=1.02
        )
        plt.tight_layout()
        plt.show()
