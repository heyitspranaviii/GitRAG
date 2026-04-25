from __future__ import annotations
import re, pickle
from pathlib import Path
from rank_bm25 import BM25Okapi
from gitrag.core.types import Chunk
from gitrag.core.logging import get_logger

logger = get_logger(__name__)

def _tokenize(text: str) -> list[str]:
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"_", " ", text)
    return re.findall(r"[a-z0-9]+", text.lower())

class BM25Store:
    def __init__(self, save_path: str = ".chroma/bm25.pkl") -> None:
        self.save_path = Path(save_path)
        self.chunks: list[Chunk] = []
        self.bm25:   BM25Okapi | None = None

    def build(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        corpus = [_tokenize(c.raw_text + " " + c.symbol_name) for c in chunks]
        self.bm25 = BM25Okapi(corpus)
        self._save()
        logger.info("bm25_built", chunk_count=len(chunks))

    def query(self, text: str, top_k: int = 20) -> list[dict]:
        if not self.bm25 or not self.chunks: return []
        scores  = self.bm25.get_scores(_tokenize(text))
        top_idx = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        return [{
            "text": self.chunks[i].raw_text,
            "meta": {"symbol": self.chunks[i].symbol_name, "file": self.chunks[i].file,
                     "language": self.chunks[i].language, "start_line": self.chunks[i].start_line,
                     "end_line": self.chunks[i].end_line, "chunk_type": self.chunks[i].chunk_type.value,
                     "docstring": self.chunks[i].docstring, "semgrep_flags": ""},
            "score": float(scores[i]), "chunk_id": self.chunks[i].chunk_id,
        } for i in top_idx if scores[i] > 0]

    def _save(self) -> None:
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.save_path, "wb") as f:
            pickle.dump({"chunks": self.chunks, "bm25": self.bm25}, f)

    def load(self) -> bool:
        if not self.save_path.exists(): return False
        with open(self.save_path, "rb") as f:
            data = pickle.load(f)
        self.chunks = data["chunks"]
        self.bm25   = data["bm25"]
        logger.info("bm25_loaded", chunk_count=len(self.chunks))
        return True
