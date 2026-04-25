from __future__ import annotations
from sentence_transformers import SentenceTransformer
from gitrag.embeddings.base import BaseEmbedder
from gitrag.core.logging import get_logger

logger = get_logger(__name__)

class Embedder(BaseEmbedder):
    def __init__(self,model_name: str = "BAAI/bge-base-en-v1.5")->None:
        logger.info("embedder_loading",model=model_name)
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        logger.info("embedder_ready",dim=self.dim)

    def embed(self,texts:list[str])->list[list[float]]:
        if not texts: 
            return []
        
        vecs = self.model.encode(
            texts,batch_size = 32,
            normalize_embeddings = True,
            show_progress_bar = len(texts) > 1000,
        )
        return vecs.tolist()

    def embed_one(self,text:str)->list[float]:
        return self.embed([text])[0]

    @property
    def dim(self) -> int:
        return self.model.get_sentence_embedding_dimension()
