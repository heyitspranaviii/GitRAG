from __future__ import annotations
import re, pickle
from pathlib import Path
import networkx as nx
from gitrag.core.types import Chunk, RawFile
from gitrag.core.logging import get_logger

logger = get_logger(__name__)

def _extract_imports(content: str, language: str) -> list[str]:
    imports = []
    if language == "python":
        for m in re.finditer(r"^(?:from|import)\s+([\w.]+)", content, re.MULTILINE):
            imports.append(m.group(1).split(".")[0])
    elif language in ("javascript","typescript"):
        for m in re.finditer(r"""(?:import|require)\s*\(?['"]([^'"]+)['"]""", content):
            imports.append(m.group(1))
    elif language == "java":
        for m in re.finditer(r"^import\s+([\w.]+);", content, re.MULTILINE):
            imports.append(m.group(1).split(".")[-1])
    elif language == "go":
        for m in re.finditer(r'"([^"]+)"', content):
            imports.append(m.group(1).split("/")[-1])
    elif language == "rust":
        for m in re.finditer(r"^use\s+([\w:]+)", content, re.MULTILINE):
            imports.append(m.group(1).split("::")[-1])
    elif language == "csharp":
        for m in re.finditer(r"^using\s+([\w.]+);", content, re.MULTILINE):
            imports.append(m.group(1).split(".")[-1])
    return imports

class GraphStore:
    def __init__(self, save_path: str = ".chroma/graph.pkl") -> None:
        self.save_path = Path(save_path)
        self.G = nx.DiGraph()
        self._file_to_chunks: dict[str, list[str]] = {}

    def build(self, chunks: list[Chunk], raw_files: list[RawFile]) -> None:
        fc = {f.path: (f.content, f.language) for f in raw_files}
        for fpath, (content, lang) in fc.items():
            self.G.add_node(fpath, kind="file")
            for imp in _extract_imports(content, lang):
                for candidate in fc:
                    if imp in candidate:
                        self.G.add_edge(fpath, candidate, kind="imports"); break
        for c in chunks:
            self._file_to_chunks.setdefault(c.file, []).append(c.chunk_id)
        self._save()
        logger.info("graph_built", nodes=self.G.number_of_nodes(), edges=self.G.number_of_edges())

    def neighbors(self, file_path: str, hops: int = 1) -> list[str]:
        if file_path not in self.G: return []
        visited, frontier = set(), {file_path}
        for _ in range(hops):
            nxt = set()
            for f in frontier:
                for nb in list(self.G.successors(f)) + list(self.G.predecessors(f)):
                    if nb not in visited: nxt.add(nb)
            visited |= nxt; frontier = nxt
        ids: list[str] = []
        for f in visited: ids.extend(self._file_to_chunks.get(f, []))
        return ids

    def _save(self) -> None:
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.save_path, "wb") as f:
            pickle.dump({"G": self.G, "f2c": self._file_to_chunks}, f)

    def load(self) -> bool:
        if not self.save_path.exists(): return False
        with open(self.save_path, "rb") as f:
            data = pickle.load(f)
        self.G = data["G"]; self._file_to_chunks = data["f2c"]
        logger.info("graph_loaded", nodes=self.G.number_of_nodes())
        return True
