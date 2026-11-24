from __future__ import annotations
from typing import List, Dict, Tuple, Any, Optional
from wptg.models.graph import Graph
from wptg.formatting.base import IGraphTableFormatter


class GraphTableFormatter:
    def _render_ascii_table(self, headers: List[str], rows: List[List[str]]) -> str:
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        sep = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
        header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"

        lines = [sep, header_line, sep]
        for row in rows:
            line = "| " + " | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)) + " |"
            lines.append(line)
        lines.append(sep)

        return "\n".join(lines)

    def format_connections(self, graph: Graph) -> str:
        headers = ["Wierzchołek", "Etykieta", "Stopień", "Połączenia (Sąsiedzi)"]
        rows: List[List[str]] = []

        sorted_vertices = sorted(graph.vertices, key=lambda v: v.index)
        for v in sorted_vertices:
            neighbors_info: List[str] = []
            deg = 0

            for e in graph.edges:
                is_incident = False
                neighbor_idx = None

                if graph.directed:
                    if e.u == v.index:
                        is_incident = True
                        neighbor_idx = e.v
                else:
                    if e.u == v.index:
                        is_incident = True
                        neighbor_idx = e.v
                    elif e.v == v.index:
                        is_incident = True
                        neighbor_idx = e.u

                if is_incident and neighbor_idx is not None:
                    deg += 1
                    target_v = graph.get_vertex(neighbor_idx)
                    target_lbl = target_v.label if target_v else "?"
                    desc = f"{neighbor_idx}:{target_lbl}"
                    details = []
                    if e.label:
                        details.append(f"etykieta: {e.label}")
                    if e.weight is not None:
                        details.append(f"waga: {e.weight}")
                    if details:
                        detail_str = ", ".join(details)
                        desc += f" [{detail_str}]"
                    neighbors_info.append(desc)

            neighbors_str = ", ".join(neighbors_info) if neighbors_info else "(brak połączeń)"
            rows.append([str(v.index), str(v.label), str(deg), neighbors_str])

        return self._render_ascii_table(headers, rows)

    def format_adjacency_matrix(self, graph: Graph) -> str:
        sorted_vertices = sorted(graph.vertices, key=lambda v: v.index)
        vertex_labels = [f"{v.index}:{v.label}" for v in sorted_vertices]
        headers = ["Wierzchołek"] + vertex_labels
        rows: List[List[str]] = []

        idx_to_pos = {v.index: i for i, v in enumerate(sorted_vertices)}
        n = len(sorted_vertices)
        matrix = [["0"] * n for _ in range(n)]

        for i in range(n):
            matrix[i][i] = "-"

        for e in graph.edges:
            if e.u in idx_to_pos and e.v in idx_to_pos:
                u_pos = idx_to_pos[e.u]
                v_pos = idx_to_pos[e.v]
                val = "1"
                if e.label and e.weight is not None:
                    val = f"{e.label}({e.weight})"
                elif e.label:
                    val = str(e.label)
                elif e.weight is not None:
                    val = str(e.weight)

                matrix[u_pos][v_pos] = val
                if not graph.directed:
                    matrix[v_pos][u_pos] = val

        for i, v_label in enumerate(vertex_labels):
            rows.append([v_label] + matrix[i])

        return self._render_ascii_table(headers, rows)

    def format_edges(self, graph: Graph) -> str:
        headers = ["Od (u)", "Do (v)", "Etykieta (u)", "Etykieta (v)", "Etykieta krawędzi", "Waga"]
        rows: List[List[str]] = []

        for e in graph.edges:
            u_v = graph.get_vertex(e.u)
            v_v = graph.get_vertex(e.v)
            u_lbl = u_v.label if u_v else "?"
            v_lbl = v_v.label if v_v else "?"
            e_lbl = str(e.label) if e.label is not None else "-"
            e_w = str(e.weight) if e.weight is not None else "-"
            rows.append([str(e.u), str(e.v), u_lbl, v_lbl, e_lbl, e_w])

        if not rows:
            rows.append(["-", "-", "-", "-", "-", "(brak krawędzi)"])

        return self._render_ascii_table(headers, rows)

    def format_html(self, graph: Graph, mode: str = "connections") -> str:
        if mode == "matrix":
            sorted_vertices = sorted(graph.vertices, key=lambda v: v.index)
            vertex_labels = [f"{v.index}:{v.label}" for v in sorted_vertices]
            headers = ["Wierzchołek"] + vertex_labels
            idx_to_pos = {v.index: i for i, v in enumerate(sorted_vertices)}
            n = len(sorted_vertices)
            matrix = [["0"] * n for _ in range(n)]
            for i in range(n):
                matrix[i][i] = "-"
            for e in graph.edges:
                if e.u in idx_to_pos and e.v in idx_to_pos:
                    u_pos = idx_to_pos[e.u]
                    v_pos = idx_to_pos[e.v]
                    val = "1"
                    if e.label and e.weight is not None:
                        val = f"{e.label} ({e.weight})"
                    elif e.label:
                        val = str(e.label)
                    elif e.weight is not None:
                        val = str(e.weight)
                    matrix[u_pos][v_pos] = val
                    if not graph.directed:
                        matrix[v_pos][u_pos] = val
            rows = [[vertex_labels[i]] + matrix[i] for i in range(n)]
        elif mode == "edges":
            headers = ["Od (u)", "Do (v)", "Etykieta (u)", "Etykieta (v)", "Etykieta krawędzi", "Waga"]
            rows = []
            for e in graph.edges:
                u_v = graph.get_vertex(e.u)
                v_v = graph.get_vertex(e.v)
                rows.append([
                    str(e.u),
                    str(e.v),
                    u_v.label if u_v else "?",
                    v_v.label if v_v else "?",
                    str(e.label) if e.label is not None else "-",
                    str(e.weight) if e.weight is not None else "-"
                ])
        else:
            headers = ["Wierzchołek", "Etykieta", "Stopień", "Połączenia (Sąsiedzi)"]
            rows = []
            sorted_vertices = sorted(graph.vertices, key=lambda v: v.index)
            for v in sorted_vertices:
                deg = 0
                neighbors_info = []
                for e in graph.edges:
                    is_incident = False
                    neighbor_idx = None
                    if graph.directed:
                        if e.u == v.index:
                            is_incident = True
                            neighbor_idx = e.v
                    else:
                        if e.u == v.index:
                            is_incident = True
                            neighbor_idx = e.v
                        elif e.v == v.index:
                            is_incident = True
                            neighbor_idx = e.u

                    if is_incident and neighbor_idx is not None:
                        deg += 1
                        target_v = graph.get_vertex(neighbor_idx)
                        target_lbl = target_v.label if target_v else "?"
                        desc = f"<b>{neighbor_idx}</b> ({target_lbl})"
                        details = []
                        if e.label:
                            details.append(f"etykieta: {e.label}")
                        if e.weight is not None:
                            details.append(f"waga: {e.weight}")
                        if details:
                            detail_str = ", ".join(details)
                            desc += f" <small>[{detail_str}]</small>"
                        neighbors_info.append(desc)

                neighbors_str = ", ".join(neighbors_info) if neighbors_info else "<i>brak</i>"
                rows.append([str(v.index), str(v.label), str(deg), neighbors_str])

        html_lines = [
            '<table style="border-collapse: collapse; width: 100%; font-family: monospace; font-size: 13px; margin: 10px 0;">',
            '  <thead>',
            '    <tr style="background-color: #1e293b; color: #f8fafc;">',
        ]
        for h in headers:
            html_lines.append(f'      <th style="border: 1px solid #cbd5e1; padding: 6px 10px; text-align: left;">{h}</th>')
        html_lines.append('    </tr>')
        html_lines.append('  </thead>')
        html_lines.append('  <tbody>')
        for r_idx, row in enumerate(rows):
            bg = "#f8fafc" if r_idx % 2 == 0 else "#ffffff"
            html_lines.append(f'    <tr style="background-color: {bg}; color: #0f172a;">')
            for cell in row:
                html_lines.append(f'      <td style="border: 1px solid #e2e8f0; padding: 6px 10px;">{cell}</td>')
            html_lines.append('    </tr>')
        html_lines.append('  </tbody>')
        html_lines.append('</table>')
        return "\n".join(html_lines)
