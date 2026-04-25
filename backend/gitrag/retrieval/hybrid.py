from __future__ import annotations
from gitrag.index.vector_store import VectorStore
from gitrag.index.bm25_store import BM25Store
from gitrag.index.graph_store import GraphStore
from gitrag.embeddings.local import Embedder
from gitrag.retrieval.fusion import rrf
from gitrag.core.logging import get_logger

logger = get_logger(__name__)

def _key(item: dict) -> str:
    if "chunk_id" in item: return item["chunk_id"]
    m = item.get("meta", {})
    return m.get("symbol","") + m.get("file","")

class HybridRetriever:
    def __init__(self, vs: VectorStore, bm25: BM25Store, graph: GraphStore, emb: Embedder, settings) -> None:
        self.vs    = vs
        self.bm25  = bm25
        self.graph = graph
        self.emb   = emb
        self.cfg   = settings.retrieval

    def retrieve(self, query: str) -> list[dict]:
        q_vec        = self.emb.embed_one(query)
        vec_results  = self.vs.query(q_vec, top_k=self.cfg.vector_top_k)
        bm25_results = self.bm25.query(query, top_k=self.cfg.bm25_top_k)
        merged       = rrf([vec_results, bm25_results])
        seen         = {_key(r) for r in merged}
        top_files    = list(dict.fromkeys(r["meta"]["file"] for r in merged[:5]))
        for fpath in top_files:
            for r in vec_results + bm25_results:
                k = _key(r)
                if k not in seen and r["meta"].get("file","") in self.graph.neighbors(fpath, self.cfg.graph_hops):
                    merged.append(r); seen.add(k)
        logger.debug("retrieval_done", candidates=len(merged[:30]))
        return merged[:30]
