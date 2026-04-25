from __future__ import annotations

import os
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RetrievalSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="")
    vector_top_k: int = Field(20, alias="VECTOR_TOP_K")
    bm25_top_k:   int = Field(20, alias="BM25_TOP_K")
    rerank_top_k: int = Field(5,  alias="RERANK_TOP_K")
    graph_hops:   int = Field(1,  alias="GRAPH_HOPS")


class FlowTracerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FLOW_")
    max_depth:      int  = Field(6,     alias="FLOW_MAX_DEPTH")
    max_children:   int  = Field(10,    alias="FLOW_MAX_CHILDREN")
    skip_externals: bool = Field(False, alias="FLOW_SKIP_EXTERNALS")


class GenerationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GEN_")
    max_tokens:    int   = Field(2048, alias="GEN_MAX_TOKENS")
    temperature:   float = Field(0.1,  alias="GEN_TEMPERATURE")
    context_limit: int   = Field(6000, alias="GEN_CONTEXT_LIMIT")


class Settings(BaseSettings):
    """
    Central application settings — loaded from environment variables.
    All values can be overridden via .env file or environment.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM
    ollama_host:      str = Field("http://localhost:11434", alias="OLLAMA_HOST")
    llm_model:        str = Field("codellama:7b",           alias="LLM_MODEL")

    # Embedding
    embedding_model:  str = Field("BAAI/bge-base-en-v1.5",  alias="EMBEDDING_MODEL")
    reranker_model:   str = Field("BAAI/bge-reranker-base",  alias="RERANKER_MODEL")

    # Storage
    chroma_path:      str = Field(".chroma",                 alias="CHROMA_PATH")
    memory_path:      str = Field(".memory",                 alias="MEMORY_PATH")
    repos_path:       str = Field("./repos",                 alias="REPOS_PATH")
    semgrep_rules:    str = Field("gitrag/semgrep_ext/rules/", alias="SEMGREP_RULES")

    # API
    api_host:         str = Field("0.0.0.0",                 alias="API_HOST")
    api_port:         int = Field(8000,                      alias="API_PORT")
    api_workers:      int = Field(1,                         alias="API_WORKERS")
    cors_origins:     str = Field("http://localhost:3000",   alias="CORS_ORIGINS")

    # Logging
    log_level:        str = Field("INFO",                    alias="LOG_LEVEL")
    log_format:       str = Field("json",                    alias="LOG_FORMAT")

    # Sub-settings (derived)
    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def retrieval(self) -> RetrievalSettings:
        return RetrievalSettings()

    @property
    def flow_tracer(self) -> FlowTracerSettings:
        return FlowTracerSettings()

    @property
    def generation(self) -> GenerationSettings:
        return GenerationSettings()


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings (singleton)."""
    return Settings()
