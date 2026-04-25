from __future__ import annotations
import chromadb
from chromadb.config import Settings as ChromaSettings
from gitrag.core.types import Chunk
from gitrag.core.logging import get_logger

logger = get_logger(__name__)

class VectorStore:
    def __init__(self, chroma_path: str = ".chroma") -> None:
        self.client = chromadb.PersistentClient(
            path=chroma_path,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="gitrag", metadata={"hnsw:space": "cosine"},
        )
        logger.info("vector_store_ready", path=chroma_path, count=self.collection.count())

    def add(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if not chunks: return
        ids   = [c.chunk_id for c in chunks]
        docs  = [c.raw_text  for c in chunks]
        metas = [{
            "symbol": c.symbol_name, "file": c.file, "language": c.language,
            "start_line": c.start_line, "end_line": c.end_line,
            "chunk_type": c.chunk_type.value, "docstring": c.docstring[:500],
            "semgrep_flags": "",
        } for c in chunks]
        for i in range(0, len(ids), 500):
            self.collection.upsert(
                ids=ids[i:i+500], documents=docs[i:i+500],
                embeddings=embeddings[i:i+500], metadatas=metas[i:i+500],
            )
        logger.info("vectors_upserted", count=len(ids))

    def query(self, embedding: list[float], top_k: int = 20) -> list[dict]:
        count = self.collection.count()
        if count == 0: return []
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=min(top_k, count),
            include=["documents","metadatas","distances"],
        )
        return [{
            "text": doc, "meta": meta, "score": 1 - dist,
            "chunk_id": meta.get("symbol","") + meta.get("file",""),
        } for doc, meta, dist in zip(
            results["documents"][0], results["metadatas"][0], results["distances"][0]
        )]

    def count(self) -> int:
        return self.collection.count()

    def update_metadata(self, chunk_id: str, updates: dict) -> None:
        try: self.collection.update(ids=[chunk_id], metadatas=[updates])
        except Exception: pass
