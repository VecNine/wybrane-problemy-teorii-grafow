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

if __name__ == "__main__":
    run_demonstration()
