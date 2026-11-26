from __future__ import annotations
import json
from typing import Optional, List
from wptg.models.graph import Graph
from wptg.models.grammar import Grammar
from wptg.transformation.system import TransformationSystem
from wptg.cli.loader import JsonResourceLoader


class TerminalApp:
    def __init__(self, loader: Optional[JsonResourceLoader] = None):
        self.loader = loader or JsonResourceLoader()

    def _prompt(self, message: str, default: Optional[str] = None) -> Optional[str]:
        try:
            value = input(message).strip()
        except (EOFError, KeyboardInterrupt):
            return None
        if not value and default is not None:
            return default
        return value

    def _choose_from_list(self, title: str, items: List[str], allow_start_graph: bool = False) -> Optional[str]:
        print(f"\n=== {title} ===")
        if allow_start_graph:
            print("  [0] Graf startowy gramatyki (startGraph)")
        for i, name in enumerate(items, 1):
            print(f"  [{i}] {name}")
        print("  [q] Wyjście")
        print("Możesz wpisać numer z listy lub podać własną ścieżkę do pliku JSON.")

        while True:
            choice = self._prompt("Wybór: ")
            if choice is None or choice.lower() == "q":
                return None
            if allow_start_graph and choice == "0":
                return "__START_GRAPH__"
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(items):
                    return items[idx]
                print("Nieprawidłowy numer z listy. Spróbuj ponownie.")
                continue
            if choice:
                return choice
            print("Podaj numer z listy lub ścieżkę do pliku.")

    def _load_grammar_interactive(self, initial_path: Optional[str] = None) -> Optional[Grammar]:
        if initial_path:
            try:
                return self.loader.load_grammar(initial_path)
            except (OSError, json.JSONDecodeError, ValueError) as err:
                print(f"Błąd wczytywania gramatyki '{initial_path}': {err}")

        grammars, _ = self.loader.discover_resources(".")
        while True:
            selected = self._choose_from_list("Wybór gramatyki", grammars)
            if selected is None:
                return None
            try:
                return self.loader.load_grammar(selected)
            except (OSError, json.JSONDecodeError, ValueError) as err:
                print(f"Błąd wczytywania gramatyki: {err}")

    def _load_graph_interactive(self, grammar: Grammar, initial_path: Optional[str] = None) -> Optional[Graph]:
        if initial_path:
            try:
                return self.loader.load_graph(initial_path)
            except (OSError, json.JSONDecodeError, ValueError) as err:
                print(f"Błąd wczytywania grafu '{initial_path}': {err}")

        _, graphs = self.loader.discover_resources(".")
        while True:
            selected = self._choose_from_list("Wybór grafu początkowego", graphs, allow_start_graph=True)
            if selected is None:
                return None
            if selected == "__START_GRAPH__":
                return grammar.start_graph.copy()
            try:
                return self.loader.load_graph(selected)
            except (OSError, json.JSONDecodeError, ValueError) as err:
                print(f"Błąd wczytywania grafu: {err}")

    def _choose_table_mode(self) -> str:
        print("Tryb tabeli: [1] połączenia (domyślny), [2] macierz sąsiedztwa, [3] lista krawędzi")
        choice = self._prompt("Wybór trybu [1]: ", default="1")
        if choice == "2":
            return "matrix"
        if choice == "3":
            return "edges"
        return "connections"

    def _print_productions_summary(self, grammar: Grammar) -> None:
        print("\nDostępne produkcje:")
        for p in grammar.productions:
            desc = f" - {p.description}" if p.description else ""
            print(f"  {p.name}{desc}")

    def _action_apply(self, ts: TransformationSystem) -> None:
        self._print_productions_summary(ts.T)
        seq = self._prompt("Podaj kolejność produkcji (np. P1, p3, 4 lub 1, 3, 4): ")
        if not seq:
            print("Nie podano żadnych produkcji.")
            return

        strat_raw = self._prompt("Strategia selekcji (1=wszystkie rosnąco, 2=najniższy indeks) [2]: ", default="2")
        if strat_raw is None:
            return
        dang_raw = self._prompt("Wiszące krawędzie (1=anuluj, 2=usuń, Enter=domyślna gramatyki): ", default="")
        if dang_raw is None:
            return

        try:
            strategy = int(strat_raw)
            dangling = int(dang_raw) if dang_raw else None
            applied = ts.apply(seq, selection_strategy=strategy, dangling_edges_handling=dangling)
        except ValueError as err:
            print(f"Błąd wykonania: {err}")
            return

        print(f"\nWykonano kroków: {len(applied)}")
        start_idx = len(ts.History) - len(applied)
        for offset, (prod, g_step) in enumerate(applied):
            v_str = ", ".join(f"{v.index}:{v.label}" for v in g_step.vertices)
            print(f"  Krok {start_idx + offset + 1} [{prod.name}]: wierzchołki=[{v_str}] | krawędzie={len(g_step.edges)}")

    def _action_visualize(self, ts: TransformationSystem) -> None:
        print("\nWizualizacja: [1] aktualny graf, [2] porównanie start vs koniec, [3] historia krok po kroku")
        choice = self._prompt("Wybór [2]: ", default="2")
        if choice is None:
            return
        try:
            if choice == "1":
                ts.G.visualize()
            elif choice == "3":
                if not ts.History:
                    ts.G.visualize(title="Stan początkowy (brak zastosowanych produkcji)")
                else:
                    ts.visualize_history(include_initial=True)
            else:
                ts.visualize_initial_and_final()
        except Exception as err:
            print(f"Błąd wizualizacji graficznej: {err}")

    def _session_loop(self, grammar: Grammar, initial_graph: Graph) -> str:
        ts = TransformationSystem(G=initial_graph.copy(), T=grammar)
        while True:
            print(
                f"\n--- Stan systemu: gramatyka='{grammar.name}' | "
                f"graf={len(ts.G.vertices)} w., {len(ts.G.edges)} k. | kroki={len(ts.History)} ---"
            )
            print("  [1] Zastosuj sekwencję produkcji")
            print("  [2] Wyświetl aktualny graf (tabela)")
            print("  [3] Porównaj graf początkowy i końcowy (tabele)")
            print("  [4] Wyświetl historię krok po kroku (tabele)")
            print("  [5] Wizualizacja graficzna (wykres)")
            print("  [6] Resetuj graf do stanu początkowego")
            print("  [7] Zmień gramatykę lub graf początkowy")
            print("  [0] Zakończ")

            action = self._prompt("Wybierz akcję: ")
            if action is None or action == "0":
                return "exit"
            if action == "1":
                self._action_apply(ts)
            elif action == "2":
                ts.G.print_table(mode=self._choose_table_mode())
            elif action == "3":
                ts.print_initial_and_final_tables(mode=self._choose_table_mode())
            elif action == "4":
                if not ts.History:
                    print("Historia jest pusta. Zastosuj najpierw produkcje.")
                else:
                    ts.print_history_tables(mode=self._choose_table_mode())
            elif action == "5":
                self._action_visualize(ts)
            elif action == "6":
                ts = TransformationSystem(G=initial_graph.copy(), T=grammar)
                print("Zresetowano graf do stanu początkowego.")
            elif action == "7":
                return "reload"
            else:
                print("Nieznana opcja. Wybierz numer od 0 do 7.")

    def run_interactive(self, grammar_path: Optional[str] = None, graph_path: Optional[str] = None) -> None:
        print("==================================================")
        print(" WPTG 2026-2027 - Aplikacja Terminalowa (Gramatyki Grafowe)")
        print("==================================================")

        cur_grammar_path = grammar_path
        cur_graph_path = graph_path

        while True:
            grammar = self._load_grammar_interactive(cur_grammar_path)
            if grammar is None:
                print("Zakończono.")
                return
            initial_graph = self._load_graph_interactive(grammar, cur_graph_path)
            if initial_graph is None:
                print("Zakończono.")
                return

            cur_grammar_path = None
            cur_graph_path = None

            status = self._session_loop(grammar, initial_graph)
            if status == "exit":
                print("Zakończono.")
                return

    def run_batch(
        self,
        grammar_path: str,
        productions: str,
        graph_path: Optional[str] = None,
        strategy: int = 2,
        dangling: Optional[int] = None,
        table_mode: str = "connections"
    ) -> None:
        grammar = self.loader.load_grammar(grammar_path)
        initial_graph = self.loader.load_graph(graph_path) if graph_path else grammar.start_graph.copy()
        ts = TransformationSystem(G=initial_graph, T=grammar)
        applied = ts.apply(productions, selection_strategy=strategy, dangling_edges_handling=dangling)
        print(f"Gramatyka: {grammar.name}")
        print(f"Sekwencja: {productions} | Wykonane kroki: {len(applied)}")
        ts.print_initial_and_final_tables(mode=table_mode)
        if ts.History:
            ts.print_history_tables(mode=table_mode)
