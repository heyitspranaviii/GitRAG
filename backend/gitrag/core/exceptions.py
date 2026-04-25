from __future__ import annotations


class GitRAGError(Exception):
    """Base exception for all GitRAG errors."""


class RepoNotFoundError(GitRAGError):
    """Raised when a repository path does not exist."""


class IndexNotFoundError(GitRAGError):
    """Raised when no index has been built yet (ingest must run first)."""


class IngestionError(GitRAGError):
    """Raised when ingestion fails mid-way."""


class LLMUnavailableError(GitRAGError):
    """Raised when Ollama is not reachable or model not pulled."""


class EmbeddingError(GitRAGError):
    """Raised when the embedding model fails."""


class SymbolNotFoundError(GitRAGError):
    """Raised by flow tracer when symbol cannot be resolved."""
