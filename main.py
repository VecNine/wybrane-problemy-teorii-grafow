import json
from wptg import (
    Graph,
    Vertex,
    Edge,
    Production,
    Grammar,
    DanglingEdges,
    SelectionStrategy,
    DanglingEdgesHandling,
    TransformationSystem,
)

grammar_json = """{
  "grammar": {
    "name": "Gramatyka ścieżek",
    "directed": false,
    "danglingEdges": "forbid",
    "labels": {
      "nonterminals": ["S", "A"],
      "terminals": ["a", "b"]
    },
    "startGraph": {
      "vertices": [{ "index": 0, "label": "S" }],
      "edges": []
    },
    "productions": [
      {
        "name": "P1",
        "description": "S -> A - S",
        "left": { "vertices": [{ "index": 0, "label": "S" }], "edges": [] },
        "right": {
          "vertices": [{ "index": 0, "label": "A" }, { "index": 1, "label": "S" }],
          "edges": [{ "u": 0, "v": 1 }]
        },
        "mapping": [],
        "embedding": [{ "leftVertex": 0, "neighborLabel": "*", "connectTo": [0] }]
      },
      {
        "name": "P2",
        "description": "A -> a",
        "left": { "vertices": [{ "index": 0, "label": "A" }], "edges": [] },
        "right": { "vertices": [{ "index": 0, "label": "a" }], "edges": [] },
        "mapping": [{ "left": 0, "right": 0 }],
        "embedding": []
      },
      {
        "name": "P3",
        "description": "S -> b",
        "left": { "vertices": [{ "index": 0, "label": "S" }], "edges": [] },
        "right": { "vertices": [{ "index": 0, "label": "b" }], "edges": [] },
        "mapping": [{ "left": 0, "right": 0 }],
        "embedding": []
      }
    ]
  }
}"""

def run_demonstration():
    gram = Grammar.from_dict(json.loads(grammar_json))
    P1 = gram.get_production("P1")
    P2 = gram.get_production("P2")
    P3 = gram.get_production("P3")

    print("=== Strategia 2 (FIRST_LOWEST): P1, P1, P3, P2, P2 ===")
    ts2 = TransformationSystem(G=gram.start_graph.copy(), T=gram)
    ts2.apply([P1, P1, P3, P2, P2], selection_strategy=2, dangling_edges_handling=1)

    for i, (prod, g) in enumerate(ts2.History):
        v_str = ", ".join(f"{v.index}:{v.label}" for v in g.vertices)
        e_str = ", ".join(f"({e.u},{e.v})" for e in g.edges)
        print(f"Krok {i+1} [{prod.name}]: wierzchołki=[{v_str}], krawędzie=[{e_str}]")

    print("\n=== Strategia 1 (ALL_ASCENDING): P1, P1, P3, P2 ===")
    ts1 = TransformationSystem(G=gram.start_graph.copy(), T=gram)
    ts1.apply([P1, P1, P3, P2], selection_strategy=1, dangling_edges_handling=1)

    for i, (prod, g) in enumerate(ts1.History):
        v_str = ", ".join(f"{v.index}:{v.label}" for v in g.vertices)
        e_str = ", ".join(f"({e.u},{e.v})" for e in g.edges)
        print(f"Krok {i+1} [{prod.name}]: wierzchołki=[{v_str}], krawędzie=[{e_str}]")

    print("\n=== Reprezentacja tabelkowa wynikowego grafu (tabela połączeń) ===")
    ts2.G.print_table(mode="connections")

    print("\n=== Reprezentacja macierzowa wynikowego grafu (macierz sąsiedztwa) ===")
    ts2.G.print_table(mode="matrix")

    print("\n=== Historia transformacji w postaci tabel połączeń ===")
    ts2.print_history_tables(mode="connections")


def run_custom_voronoi_sequence():
    with open("graf_voronoi_ABCDE.json", "r", encoding="utf-8") as f:
        g_voronoi = Graph.from_dict(json.load(f))
    with open("gramatyka_ABCDE.json", "r", encoding="utf-8") as f:
        gram_abcde = Grammar.from_dict(json.load(f))

    print("\n=== Tryb własnej kolejności produkcji (Gramatyka ABCDE + Graf Voronoia) ===")
    print("Dostępne produkcje:", ", ".join(p.name for p in gram_abcde.productions))
    default_seq = "P1, P6, P11"

    try:
        user_seq = input(f"Podaj kolejność produkcji (np. P1, P6, P11) [Enter = {default_seq}]: ").strip()
    except EOFError:
        user_seq = ""

    seq = user_seq if user_seq else default_seq
    ts_custom = TransformationSystem(G=g_voronoi.copy(), T=gram_abcde)
    ts_custom.apply(seq, selection_strategy=2, dangling_edges_handling=1)

    print("\n=== Porównanie grafu początkowego i końcowego ===")
    ts_custom.print_initial_and_final_tables(mode="connections")


if __name__ == "__main__":
    run_demonstration()
    run_custom_voronoi_sequence()
