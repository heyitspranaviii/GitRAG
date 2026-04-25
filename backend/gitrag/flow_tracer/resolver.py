from __future__ import annotations

import networkx as nx
from rapidfuzz import fuzz, process


class SymbolResolver:
    def __init__(self, graph: nx.DiGraph) -> None:
        self.G           = graph
        self.all_symbols = list(graph.nodes())

    def resolve(self, name: str, threshold: int = 65) -> str | None:
        if not name:
            return None
        if name in self.G:
            return name
        suffix = [s for s in self.all_symbols
                  if s == name or s.endswith(f".{name}") or s.endswith(f"_{name}") or s.lower() == name.lower()]
        if len(suffix) == 1:
            return suffix[0]
        if len(suffix) > 1:
            best, score, _ = process.extractOne(name, suffix, scorer=fuzz.ratio)
            return best if score >= threshold else None
        if not self.all_symbols:
            return None
        best, score, _ = process.extractOne(name, self.all_symbols, scorer=fuzz.token_sort_ratio)
        return best if score >= threshold else None

    def suggest(self, name: str, top_k: int = 3) -> list[str]:
        if not self.all_symbols:
            return []
        results = process.extract(name, self.all_symbols, scorer=fuzz.token_sort_ratio, limit=top_k)
        return [sym for sym, score, _ in results if score >= 40]
