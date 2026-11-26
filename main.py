import argparse
from wptg import TerminalApp


def parse_args():
    parser = argparse.ArgumentParser(description="WPTG - System transformacji grafowych")
    parser.add_argument("-T", "--grammar", help="Ścieżka do pliku gramatyki JSON")
    parser.add_argument("-G", "--graph", help="Ścieżka do pliku grafu początkowego JSON")
    parser.add_argument("-p", "--productions", help="Kolejność produkcji (np. 'P1, p3, 4' lub '1, 3, 4')")
    parser.add_argument("-s", "--strategy", type=int, default=2, choices=[1, 2], help="Strategia selekcji (1 lub 2)")
    parser.add_argument("-d", "--dangling", type=int, choices=[1, 2], help="Obsługa wiszących krawędzi (1=anuluj, 2=usuń)")
    parser.add_argument(
        "-m",
        "--mode",
        default="connections",
        choices=["connections", "matrix", "edges"],
        help="Tryb wyświetlania tabel"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    app = TerminalApp()
    if args.grammar and args.productions:
        app.run_batch(
            grammar_path=args.grammar,
            productions=args.productions,
            graph_path=args.graph,
            strategy=args.strategy,
            dangling=args.dangling,
            table_mode=args.mode
        )
    else:
        app.run_interactive(grammar_path=args.grammar, graph_path=args.graph)


if __name__ == "__main__":
    main()
