from __future__ import annotations
from typing import Optional, List, Tuple, Union, Any
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
        self.G = G
        self.T = T
        self.History: List[Tuple[Production, Graph]] = []
        self.history = self.History
        self.matcher = matcher or GraphMatcher()
        self.applier = applier or ProductionApplier()

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

    def apply(
        self,
        productions: List[Union[Production, str]],
        selection_strategy: Optional[Union[SelectionStrategy, int]] = None,
        dangling_edges_handling: Optional[Union[DanglingEdgesHandling, int]] = None
    ) -> List[Tuple[Production, Graph]]:
        sel_strat = self._resolve_selection_strategy(selection_strategy)

        newly_applied: List[Tuple[Production, Graph]] = []

        for item in productions:
            prod = self._resolve_production(item)
            dang_strat = self._resolve_dangling_strategy(dangling_edges_handling, prod)
            matches = self.matcher.find_matches(self.G, prod.left)
            selected_matches = sel_strat.select(matches)

            for match in selected_matches:
                target_still_present = all(
                    self.G.get_vertex(g_idx) is not None
                    for g_idx in match.values()
                )
                if not target_still_present:
                    continue

                transformed = self.applier.apply(self.G, prod, match, dang_strat)
                if transformed is not None:
                    self.G = transformed
                    record = (prod, self.G.copy())
                    self.History.append(record)
                    newly_applied.append(record)

        return newly_applied

    def visualize_history(self, figsize_per_step: tuple = (4.5, 3.5)):
        import matplotlib.pyplot as plt

        if not self.History:
            return
        total_steps = len(self.History)
        cols = min(3, total_steps)
        rows = (total_steps + cols - 1) // cols
        fig, axes = plt.subplots(rows, cols, figsize=(cols * figsize_per_step[0], rows * figsize_per_step[1]))
        if total_steps == 1:
            axes = [axes]
        else:
            axes = axes.flatten() if hasattr(axes, "flatten") else [axes]

        for i, (prod, g) in enumerate(self.History):
            g.visualize(title=f"Krok {i+1}: {prod.name}", ax=axes[i])

        for j in range(total_steps, len(axes)):
            axes[j].axis("off")

        plt.suptitle("Historia transformacji grafu", fontsize=14, fontweight="bold", y=1.02)
        plt.tight_layout()
        plt.show()



    def print_history_tables(self, mode: str = "connections") -> None:
        for i, (prod, g) in enumerate(self.History):
            print(f"\n--- Krok {i+1}: Produkcja {prod.name} ---")
            g.print_table(mode=mode)

    def display_history_tables(self, mode: str = "connections") -> None:
        try:
            from IPython.display import display, HTML
            html_parts = []
            for i, (prod, g) in enumerate(self.History):
                header_html = f"<h4 style=\x27margin-top:15px;\x27>Krok {i+1}: Produkcja {prod.name}</h4>"
                html_parts.append(header_html)
                html_parts.append(g.to_html_table(mode=mode))
            display(HTML("".join(html_parts)))
        except ImportError:
            self.print_history_tables(mode=mode)


TransormationSystem = TransformationSystem
