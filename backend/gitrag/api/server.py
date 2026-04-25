from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from gitrag.core.config import get_settings
from gitrag.core.exceptions import (
    IndexNotFoundError,
    LLMUnavailableError,
    RepoNotFoundError,
)
from gitrag.core.logging import get_logger, setup_logging
from gitrag.core.pipeline import GitRAG

settings = get_settings()
setup_logging(
    level      = settings.log_level,
    log_format = settings.log_format,
    log_file   = "/app/logs/gitrag.log",
)
logger = get_logger(__name__)

_rag: GitRAG | None = None


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _rag
    logger.info("startup_begin", model=settings.llm_model, host=settings.ollama_host)
    _rag = GitRAG(settings)
    loaded = _rag.load()
    if loaded:
        logger.info("startup_index_loaded")
    else:
        logger.info("startup_no_index", hint="POST /ingest to index a repository")
    yield
    logger.info("shutdown")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "GitRAG API",
    description = "Chat with any GitHub repository — locally, fully offline.",
    version     = "0.1.0",
    lifespan    = lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = settings.cors_origins_list,
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


# ── Request / Response models ─────────────────────────────────────────────────

class IngestRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute path to the local repository")


class IngestResponse(BaseModel):
    status:    str
    stats:     dict[str, Any]


class QueryRequest(BaseModel):
    query:      str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field("default", max_length=64)


class QueryResponse(BaseModel):
    answer:     str
    session_id: str
    elapsed_ms: float


class HealthResponse(BaseModel):
    status:     str
    ready:      bool
    model:      str
    index_size: int


class ErrorResponse(BaseModel):
    detail: str
    code:   str


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_rag() -> GitRAG:
    if _rag is None:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Service not initialised")
    return _rag


# ── Global error handler ──────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception", path=request.url.path, error=str(exc))
    return JSONResponse(
        status_code = 500,
        content     = {"detail": "Internal server error", "code": "INTERNAL_ERROR"},
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """System health check — returns readiness status and model info."""
    rag = get_rag()
    return HealthResponse(
        status     = "ok",
        ready      = rag.is_ready,
        model      = settings.llm_model,
        index_size = rag.vector_store.count(),
    )


@app.post("/ingest", response_model=IngestResponse, tags=["ingestion"])
def ingest(req: IngestRequest) -> IngestResponse:
    """
    Ingest a repository.
    Reads all source files, chunks, embeds, indexes, and runs semgrep.
    This endpoint blocks until complete (can take several minutes on CPU).
    """
    rag = get_rag()
    logger.info("ingest_request", repo_path=req.repo_path)
    try:
        stats = rag.ingest(req.repo_path)
        return IngestResponse(status="ok", stats=stats)
    except RepoNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc))
    except Exception as exc:
        logger.error("ingest_failed", error=str(exc))
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, f"Ingestion failed: {exc}")


@app.post("/query", response_model=QueryResponse, tags=["chat"])
def query(req: QueryRequest) -> QueryResponse:
    """
    Ask a question about the ingested repository.
    Runs hybrid retrieval, optional flow trace, semgrep injection, and LLM generation.
    """
    rag = get_rag()
    t   = time.perf_counter()
    logger.info("query_request", session_id=req.session_id, query_preview=req.query[:80])
    try:
        answer = rag.ask(req.query, session_id=req.session_id)
    except IndexNotFoundError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc))
    except LLMUnavailableError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(exc))
    elapsed_ms = round((time.perf_counter() - t) * 1000, 1)
    return QueryResponse(answer=answer, session_id=req.session_id, elapsed_ms=elapsed_ms)


@app.delete("/memory/{session_id}", tags=["chat"])
def clear_memory(session_id: str) -> dict:
    """Clear all conversation memory for a session."""
    from gitrag.memory.conversation import Memory
    Memory(session_id, settings.memory_path).clear()
    logger.info("memory_cleared", session_id=session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/sessions/{session_id}/turns", tags=["chat"])
def get_turns(session_id: str, last_n: int = 10) -> dict:
    """Get recent conversation turns for a session."""
    from gitrag.memory.conversation import Memory
    mem   = Memory(session_id, settings.memory_path)
    turns = mem.get_history(last_n=last_n)
    return {
        "session_id": session_id,
        "turns":      [{"role": t.role, "content": t.content} for t in turns],
        "count":      mem.turn_count(),
    }
