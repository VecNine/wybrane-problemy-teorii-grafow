from __future__ import annotations
from typing import Optional, List, Tuple, Union, Dict, Any
from wptg.models.graph import Graph
from wptg.models.production import Production
from wptg.models.grammar import Grammar
from wptg.models.enums import DanglingEdges, SelectionStrategy, DanglingEdgesHandling
from wptg.matching.base import IGraphMatcher
from wptg.matching.matcher import GraphMatcher
from wptg.transformation.base import IProductionApplier
from wptg.transformation.applier import ProductionApplier
from wptg.strategies.base import ISelectionStrategy
from wptg.strategies.selection import AllAscendingStrategy, LowestIndexStrategy


class TransformationSystem:
    def __init__(
        self,
        G: Graph,
        T: Grammar,
        matcher: Optional[IGraphMatcher] = None,
        applier: Optional[IProductionApplier] = None
    ):
        self.initial_graph = G.copy()
        self.G = G
        self.T = T
        self.History: List[Tuple[Production, Graph]] = []
        self.history = self.History
        self.matcher = matcher or GraphMatcher()
        self.applier = applier or ProductionApplier()

    def _normalize_productions(self, productions: Union[List[Union[Production, str]], str]) -> List[Union[Production, str]]:
        if isinstance(productions, str):
            cleaned = productions.replace("->", " ").replace(",", " ").replace(";", " ")
            return [token.strip() for token in cleaned.split() if token.strip()]
        return list(productions)

    def _resolve_production(self, prod: Union[Production, str]) -> Production:
        if isinstance(prod, str):
            found = self.T.get_production(prod)
            if found is None:
                raise ValueError(f"Production {prod} not found in grammar {self.T.name}")
            return found
        return prod

    def _resolve_selection_strategy(self, strategy: Optional[Union[SelectionStrategy, int]]) -> ISelectionStrategy:
        if strategy is None:
            return AllAscendingStrategy()
        if isinstance(strategy, int):
            strategy = SelectionStrategy(strategy)
        if strategy == SelectionStrategy.ALL_ASCENDING:
            return AllAscendingStrategy()
        if strategy == SelectionStrategy.FIRST_LOWEST:
            return LowestIndexStrategy()
        raise ValueError(f"Unknown selection strategy: {strategy}")

    def _resolve_dangling_strategy(
        self,
        handling: Optional[Union[DanglingEdgesHandling, int]],
        prod: Optional[Production] = None
    ) -> DanglingEdgesHandling:
        if handling is not None:
            if isinstance(handling, int):
                return DanglingEdgesHandling(handling)
            if isinstance(handling, DanglingEdges):
                return DanglingEdgesHandling.DELETE if handling == DanglingEdges.DELETE else DanglingEdgesHandling.CANCEL
            return handling
        if prod is not None and prod.dangling_edges is not None:
            return DanglingEdgesHandling.DELETE if prod.dangling_edges == DanglingEdges.DELETE else DanglingEdgesHandling.CANCEL
        if self.T.dangling_edges == DanglingEdges.DELETE:
            return DanglingEdgesHandling.DELETE
        return DanglingEdgesHandling.CANCEL

    def _is_match_valid(self, prod: Production, match: Dict[int, int]) -> bool:
        for l_idx, g_idx in match.items():
            g_v = self.G.get_vertex(g_idx)
            l_v = prod.left.get_vertex(l_idx)
            if g_v is None or l_v is None or g_v.label != l_v.label:
                return False
        return True

    def apply(
        self,
        productions: Union[List[Union[Production, str]], str],
        selection_strategy: Optional[Union[SelectionStrategy, int]] = None,
        dangling_edges_handling: Optional[Union[DanglingEdgesHandling, int]] = None
    ) -> List[Tuple[Production, Graph]]:
        sel_strat = self._resolve_selection_strategy(selection_strategy)
        normalized_productions = self._normalize_productions(productions)

        newly_applied: List[Tuple[Production, Graph]] = []

        for item in normalized_productions:
            prod = self._resolve_production(item)
            dang_strat = self._resolve_dangling_strategy(dangling_edges_handling, prod)
            matches = self.matcher.find_matches(self.G, prod.left)
            selected_matches = sel_strat.select(matches)

            for match in selected_matches:
                if not self._is_match_valid(prod, match):
                    continue

                transformed = self.applier.apply(self.G, prod, match, dang_strat)
                if transformed is not None:
                    self.G = transformed
                    record = (prod, self.G.copy())
                    self.History.append(record)
                    newly_applied.append(record)

        return newly_applied

    def visualize_history(self, figsize_per_step: tuple = (4.5, 3.5), include_initial: bool = False):
        import matplotlib.pyplot as plt

        steps: List[Tuple[str, Graph]] = []
        if include_initial:
            steps.append(("Krok 0: Stan początkowy", self.initial_graph))
        for i, (prod, g) in enumerate(self.History):
            steps.append((f"Krok {i+1}: {prod.name}", g))

        if not steps:
            return

        total_steps = len(steps)
        cols = min(3, total_steps)
        rows = (total_steps + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(cols * figsize_per_step[0], rows * figsize_per_step[1]))
        if total_steps == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

        for i, (title, g) in enumerate(steps):
            g.visualize(title=title, ax=axes[i])

        for j in range(total_steps, len(axes)):
            axes[j].axis("off")

        plt.suptitle("Historia transformacji grafu", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        plt.show()

    def visualize_initial_and_final(self, figsize: tuple = (13, 5)) -> None:
        import matplotlib.pyplot as plt

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)
        self.initial_graph.visualize(
            title=f"Stan początkowy ({len(self.initial_graph.vertices)} w., {len(self.initial_graph.edges)} k.)",
            ax=ax1
        )
        self.G.visualize(
            title=f"Stan końcowy ({len(self.G.vertices)} w., {len(self.G.edges)} k.)",
            ax=ax2
        )
        plt.suptitle("Porównanie grafu początkowego i końcowego", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        plt.show()

    def _print_graph_tables(self, items: List[Tuple[str, Graph]], mode: str = "connections") -> None:
        for title, g in items:
            print(f"\n--- {title} ---")
            g.print_table(mode=mode)

    def _display_graph_tables(self, items: List[Tuple[str, Graph]], mode: str = "connections") -> None:
        try:
            from IPython.display import display, HTML
            html_parts = []
            for title, g in items:
                header_html = f"<h4 style=\x27margin-top:15px;\x27>{title}</h4>"
                html_parts.append(header_html)
                html_parts.append(g.to_html_table(mode=mode))
            display(HTML("".join(html_parts)))
        except ImportError:
            self._print_graph_tables(items, mode=mode)

    def print_history_tables(self, mode: str = "connections") -> None:
        items = [(f"Krok {i+1}: Produkcja {prod.name}", g) for i, (prod, g) in enumerate(self.History)]
        self._print_graph_tables(items, mode=mode)

    def display_history_tables(self, mode: str = "connections") -> None:
        items = [(f"Krok {i+1}: Produkcja {prod.name}", g) for i, (prod, g) in enumerate(self.History)]
        self._display_graph_tables(items, mode=mode)

    def print_initial_and_final_tables(self, mode: str = "connections") -> None:
        items = [
            ("Stan początkowy (Pierwszy graf)", self.initial_graph),
            ("Stan końcowy (Graf wynikowy)", self.G),
        ]
        self._print_graph_tables(items, mode=mode)

    def display_initial_and_final_tables(self, mode: str = "connections") -> None:
        items = [
            ("Stan początkowy (Pierwszy graf)", self.initial_graph),
            ("Stan końcowy (Graf wynikowy)", self.G),
        ]
        self._display_graph_tables(items, mode=mode)


TransormationSystem = TransformationSystem
