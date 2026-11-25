from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Any
import copy


@dataclass
class Vertex:
    index: int
    label: str
    x: Optional[float] = None
    y: Optional[float] = None


@dataclass
class Edge:
    u: int
    v: int
    label: Optional[str] = None
    weight: Optional[float] = None


@dataclass
class Graph:
    directed: bool = False
    name: Optional[str] = None
    vertices: List[Vertex] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> Graph:
        g = data.get("graph", data)
        vertices = [
            Vertex(
                index=v["index"],
                label=v["label"],
                x=v.get("x"),
                y=v.get("y")
            )
            for v in g.get("vertices", [])
        ]
        edges = [
            Edge(u=e["u"], v=e["v"], label=e.get("label"), weight=e.get("weight"))
            for e in g.get("edges", [])
        ]
        return cls(
            directed=g.get("directed", False),
            name=g.get("name"),
            vertices=vertices,
            edges=edges
        )

    def copy(self) -> Graph:
        return copy.deepcopy(self)

    def get_vertex(self, index: int) -> Optional[Vertex]:
        for v in self.vertices:
            if v.index == index:
                return v
        return None

    def get_next_free_index(self) -> int:
        if not self.vertices:
            return 0
        return max(v.index for v in self.vertices) + 1

    def to_networkx(self) -> Any:
        import networkx as nx
        G = nx.DiGraph() if self.directed else nx.Graph()
        for v in self.vertices:
            G.add_node(v.index, label=v.label)
        for e in self.edges:
            attrs = {}
            if e.label is not None:
                attrs["label"] = e.label
            if e.weight is not None:
                attrs["weight"] = e.weight
            G.add_edge(e.u, e.v, **attrs)
        return G

    def _compute_layout(self, G: Any) -> dict:
        import math
        import networkx as nx

        if not self.vertices:
            return {}

        pos = {
            v.index: (v.x, v.y)
            for v in self.vertices
            if v.x is not None and v.y is not None
        }
        if len(pos) == len(self.vertices):
            return pos
        if not pos:
            if len(self.vertices) <= 4:
                return nx.circular_layout(G)
            return nx.spring_layout(G, seed=42, weight=None)

        xs = [p[0] for p in pos.values()]
        ys = [p[1] for p in pos.values()]
        scale = max(max(xs) - min(xs), max(ys) - min(ys), 10.0) * 0.08
        center_x = sum(xs) / len(xs)
        center_y = sum(ys) / len(ys)

        missing = [v.index for v in self.vertices if v.index not in pos]
        total_missing = max(len(missing), 1)
        placed_count = 0

        while missing:
            progressed = False
            remaining = []
            for v_idx in missing:
                if self.directed:
                    neighbor_ids = list(G.predecessors(v_idx)) + list(G.successors(v_idx))
                else:
                    neighbor_ids = list(G.neighbors(v_idx))
                nbrs = [pos[n] for n in neighbor_ids if n in pos]
                if nbrs:
                    angle = 2 * math.pi * placed_count / total_missing
                    cx = sum(p[0] for p in nbrs) / len(nbrs)
                    cy = sum(p[1] for p in nbrs) / len(nbrs)
                    pos[v_idx] = (cx + scale * math.cos(angle), cy + scale * math.sin(angle))
                    placed_count += 1
                    progressed = True
                else:
                    remaining.append(v_idx)
            if not progressed:
                for v_idx in remaining:
                    angle = 2 * math.pi * placed_count / total_missing
                    pos[v_idx] = (center_x + scale * math.cos(angle), center_y + scale * math.sin(angle))
                    placed_count += 1
                break
            missing = remaining

        return pos

    def visualize(
        self,
        title: Optional[str] = None,
        figsize: tuple = (7, 5),
        ax: Optional[Any] = None,
        pos: Optional[dict] = None,
        node_colors: Optional[dict[int, str]] = None
    ):
        import networkx as nx
        import matplotlib.pyplot as plt

        G = self.to_networkx()

        if pos is None:
            pos = self._compute_layout(G)

        show_plot = False
        if ax is None:
            plt.figure(figsize=figsize)
            ax = plt.gca()
            show_plot = True

        labels = {v.index: f"{v.index}: {v.label}" for v in self.vertices}
        colors = [
            node_colors.get(v.index, "#93c5fd") if node_colors else "#93c5fd"
            for v in self.vertices
        ]

        nx.draw_networkx_nodes(
            G, pos,
            ax=ax,
            node_color=colors,
            node_size=1600,
            edgecolors="#1e40af",
            linewidths=2
        )
        nx.draw_networkx_labels(
            G, pos,
            labels=labels,
            ax=ax,
            font_size=11,
            font_weight="bold",
            font_color="#0f172a"
        )
        nx.draw_networkx_edges(
            G, pos,
            ax=ax,
            edge_color="#475569",
            width=2,
            arrows=self.directed,
            arrowsize=20 if self.directed else 10
        )

        edge_labels = {}
        for e in self.edges:
            parts = []
            if e.label:
                parts.append(str(e.label))
            if e.weight is not None:
                parts.append(str(e.weight))
            if parts:
                edge_labels[(e.u, e.v)] = " | ".join(parts)

        if edge_labels:
            nx.draw_networkx_edge_labels(
                G, pos,
                edge_labels=edge_labels,
                ax=ax,
                font_color="#dc2626",
                font_size=10,
                font_weight="bold"
            )

        chart_title = title or self.name or "Graf"
        ax.set_title(chart_title, fontsize=13, fontweight="bold", pad=12)
        ax.margins(0.15)
        ax.axis("off")

        if show_plot:
            plt.tight_layout()
            plt.show()

    def to_table(self, mode: str = "connections") -> str:
        from wptg.formatting.table import GraphTableFormatter
        formatter = GraphTableFormatter()
        if mode == "matrix":
            return formatter.format_adjacency_matrix(self)
        elif mode == "edges":
            return formatter.format_edges(self)
        return formatter.format_connections(self)

    def to_html_table(self, mode: str = "connections") -> str:
        from wptg.formatting.table import GraphTableFormatter
        return GraphTableFormatter().format_html(self, mode=mode)

    def print_table(self, mode: str = "connections") -> None:
        print(self.to_table(mode=mode))

    def display_table(self, mode: str = "connections") -> None:
        try:
            from IPython.display import display, HTML
            display(HTML(self.to_html_table(mode=mode)))
        except ImportError:
            self.print_table(mode=mode)
