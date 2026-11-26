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

    def _neighbor_ids(self, G: Any, v_idx: int) -> List[int]:
        if self.directed:
            return list(G.predecessors(v_idx)) + list(G.successors(v_idx))
        return list(G.neighbors(v_idx))

    def _build_initial_positions(self, G: Any, raw_pos: dict) -> dict:
        import math

        xs = [p[0] for p in raw_pos.values()]
        ys = [p[1] for p in raw_pos.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span = max(max_x - min_x, max_y - min_y, 1.0)
        n = len(self.vertices)
        total_missing = max(n - len(raw_pos), 1)
        missing_idx = 0
        init_pos = {}

        for v in self.vertices:
            if v.index in raw_pos:
                nx_coord = 2 * (raw_pos[v.index][0] - min_x) / span - 1.0
                ny_coord = 2 * (raw_pos[v.index][1] - min_y) / span - 1.0
                init_pos[v.index] = (nx_coord, ny_coord)
            else:
                angle = 2 * math.pi * missing_idx / total_missing
                radius = 0.35 + 0.15 * (missing_idx % 3)
                nbrs = [raw_pos[nb] for nb in self._neighbor_ids(G, v.index) if nb in raw_pos]
                if nbrs:
                    cx = 2 * (sum(p[0] for p in nbrs) / len(nbrs) - min_x) / span - 1.0
                    cy = 2 * (sum(p[1] for p in nbrs) / len(nbrs) - min_y) / span - 1.0
                else:
                    cx, cy = 0.0, 0.0
                init_pos[v.index] = (cx + radius * math.cos(angle), cy + radius * math.sin(angle))
                missing_idx += 1

        return init_pos

    def _separate_overlapping_nodes(self, pos: dict, min_dist: float) -> dict:
        import math

        mutable = {k: [float(v[0]), float(v[1])] for k, v in pos.items()}
        keys = sorted(mutable.keys())

        for _ in range(50):
            for i, u in enumerate(keys):
                for v in keys[i + 1:]:
                    dx = mutable[u][0] - mutable[v][0]
                    dy = mutable[u][1] - mutable[v][1]
                    dist = math.hypot(dx, dy)
                    if dist < 1e-6:
                        dx, dy, dist = 1.0, 0.5, math.hypot(1.0, 0.5)
                    if dist < min_dist:
                        push = (min_dist - dist) * 0.45
                        ux, uy = (dx / dist) * push, (dy / dist) * push
                        mutable[u][0] += ux
                        mutable[u][1] += uy
                        mutable[v][0] -= ux
                        mutable[v][1] -= uy

        return {k: tuple(v) for k, v in mutable.items()}

    def _compute_layout(self, G: Any) -> dict:
        import math
        import networkx as nx

        n = len(self.vertices)
        if not n:
            return {}

        raw_pos = {
            v.index: (v.x, v.y)
            for v in self.vertices
            if v.x is not None and v.y is not None
        }
        if len(raw_pos) == n:
            return raw_pos
        if n <= 4 and not raw_pos:
            return nx.circular_layout(G)

        init_pos = self._build_initial_positions(G, raw_pos) if raw_pos else None
        k_val = 2.6 / math.sqrt(max(n, 1))
        pos = nx.spring_layout(G, pos=init_pos, k=k_val, iterations=350, seed=42, weight=None)
        min_dist = 1.6 / math.sqrt(max(n, 2))
        return self._separate_overlapping_nodes(pos, min_dist)

    def visualize(
        self,
        title: Optional[str] = None,
        figsize: Optional[tuple] = None,
        ax: Optional[Any] = None,
        pos: Optional[dict] = None,
        node_colors: Optional[dict[int, str]] = None
    ):
        import networkx as nx
        import matplotlib.pyplot as plt

        G = self.to_networkx()

        if pos is None:
            pos = self._compute_layout(G)

        n = len(self.vertices)
        if figsize is None:
            figsize = (
                max(9.0, min(14.5, 7.5 + n * 0.3)),
                max(7.0, min(10.5, 5.5 + n * 0.22)),
            )

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

        node_sz = 1350 if n > 8 else 1600
        node_font_sz = 10 if n > 8 else 11

        nx.draw_networkx_nodes(
            G, pos,
            ax=ax,
            node_color=colors,
            node_size=node_sz,
            edgecolors="#1e40af",
            linewidths=2
        )
        nx.draw_networkx_labels(
            G, pos,
            labels=labels,
            ax=ax,
            font_size=node_font_sz,
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
                font_size=9,
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
