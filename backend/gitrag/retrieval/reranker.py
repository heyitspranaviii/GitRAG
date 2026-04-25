from __future__ import annotations
from sentence_transformers import CrossEncoder
from gitrag.core.logging import get_logger

logger = get_logger(__name__)

class Reranker:
    def __init__(self, model_name: str = "BAAI/bge-reranker-base") -> None:
        logger.info("reranker_loading", model=model_name)
        self.model = CrossEncoder(model_name, max_length=512)
        logger.info("reranker_ready")

    def rerank(self, query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
        if not candidates: return []
        scores = self.model.predict([(query, c["text"]) for c in candidates])
        ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
        result = []
        for score, c in ranked[:top_k]:
            c = c.copy(); c["rerank_score"] = float(score); result.append(c)
        return result
