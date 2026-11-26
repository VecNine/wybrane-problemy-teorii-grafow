from __future__ import annotations
import glob
import json
import os
from typing import List, Tuple
from wptg.models.graph import Graph
from wptg.models.grammar import Grammar


class JsonResourceLoader:
    def _read_json(self, path: str) -> dict:
        clean_path = self.normalize_path(path)
        with open(clean_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def normalize_path(self, path: str) -> str:
        cleaned = path.strip().strip("'\"")
        if os.path.exists(cleaned):
            return cleaned
        unescaped = cleaned.replace("\\ ", " ")
        if os.path.exists(unescaped):
            return unescaped
        return cleaned

    def discover_resources(self, directory: str = ".") -> Tuple[List[str], List[str]]:
        grammars: List[str] = []
        graphs: List[str] = []
        candidates = sorted(
            glob.glob(os.path.join(directory, "*.json"))
            + glob.glob(os.path.join(directory, "*.txt"))
        )
        for path in candidates:
            try:
                data = self._read_json(path)
            except (OSError, json.JSONDecodeError, UnicodeDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            name = os.path.basename(path)
            if "grammar" in data or "productions" in data:
                grammars.append(name)
            elif "graph" in data or "vertices" in data:
                graphs.append(name)
        return grammars, graphs

    def load_grammar(self, path: str) -> Grammar:
        data = self._read_json(path)
        if not isinstance(data, dict) or ("grammar" not in data and "productions" not in data):
            raise ValueError(f"Plik '{path}' nie zawiera poprawnej definicji gramatyki.")
        return Grammar.from_dict(data)

    def load_graph(self, path: str) -> Graph:
        data = self._read_json(path)
        if not isinstance(data, dict) or ("graph" not in data and "vertices" not in data):
            raise ValueError(f"Plik '{path}' nie zawiera poprawnej definicji grafu.")
        return Graph.from_dict(data)
