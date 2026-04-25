from __future__ import annotations

import time
from typing import AsyncGenerator

from gitrag.core.config import Settings
from gitrag.core.exceptions import IndexNotFoundError, RepoNotFoundError
from gitrag.core.logging import get_logger
from gitrag.core.types import Intent, IntentType
from gitrag.ingest.loader import load_repo
from gitrag.chunking.ast_chunker import chunk_repo
from gitrag.embeddings.local import Embedder
from gitrag.index.vector_store import VectorStore
from gitrag.index.bm25_store import BM25Store
from gitrag.index.graph_store import GraphStore
from gitrag.retrieval.hybrid import HybridRetriever
from gitrag.retrieval.reranker import Reranker
from gitrag.generation.llm import LLMClient
from gitrag.generation.prompts import pick_system_prompt
from gitrag.generation.context import build_context
from gitrag.memory.conversation import Memory
from gitrag.query.intent import detect_intent
from gitrag.query.reformulator import reformulate
from gitrag.query.multi_hop import expand_multi_hop
from gitrag.semgrep_ext.runner import run_semgrep
from gitrag.semgrep_ext.tagger import tag_chunks, format_findings_for_prompt
from gitrag.flow_tracer.orchestrator import FlowTracerOrchestrator

logger = get_logger(__name__)


class GitRAG:
    """
    Master pipeline class.
    Wires every module together and exposes two public methods:
      - ingest(repo_path)
      - ask(query, session_id)
    """

    def __init__(self, settings: Settings) -> None:
        self.settings     = settings
        self.embedder     = Embedder(settings.embedding_model)
        self.vector_store = VectorStore(settings.chroma_path)
        self.bm25_store   = BM25Store(f"{settings.chroma_path}/bm25.pkl")
        self.graph_store  = GraphStore(f"{settings.chroma_path}/graph.pkl")
        self.reranker     = Reranker(settings.reranker_model)
        self.llm          = LLMClient(settings)
        self.flow_tracer  = FlowTracerOrchestrator(settings)
        self.retriever: HybridRetriever | None = None
        self.findings:  list = []
        self._ingested: bool = False

    # ── Ingestion ─────────────────────────────────────────────────────────────

    def ingest(self, repo_path: str) -> dict:
        """
        Full ingestion pipeline:
        load → chunk → embed → index → semgrep → call graph
        Returns summary statistics.
        """
        t_start = time.perf_counter()
        logger.info("ingestion_started", repo_path=repo_path)

        try:
            raw_files  = load_repo(repo_path)
            chunks     = chunk_repo(raw_files)

            logger.info("embedding_started", chunk_count=len(chunks))
            embeddings = self.embedder.embed([c.raw_text for c in chunks])

            self.vector_store.add(chunks, embeddings)
            self.bm25_store.build(chunks)
            self.graph_store.build(chunks, raw_files)

            self.findings = run_semgrep(repo_path, self.settings.semgrep_rules)
            tags = tag_chunks(chunks, self.findings)
            for chunk_id, rule_ids in tags.items():
                self.vector_store.update_metadata(
                    chunk_id, {"semgrep_flags": ",".join(rule_ids)}
                )

            self.flow_tracer.build(chunks)
            self.retriever = HybridRetriever(
                self.vector_store, self.bm25_store,
                self.graph_store, self.embedder, self.settings,
            )
            self._ingested = True

            elapsed = round(time.perf_counter() - t_start, 2)
            stats = {
                "files":    len(raw_files),
                "chunks":   len(chunks),
                "findings": len(self.findings),
                "elapsed_s": elapsed,
            }
            logger.info("ingestion_complete", **stats)
            return stats

        except FileNotFoundError as exc:
            raise RepoNotFoundError(str(exc)) from exc

    def load(self) -> bool:
        """Load existing indexes from disk without re-ingesting."""
        ok_bm25  = self.bm25_store.load()
        ok_graph = self.graph_store.load()
        if not ok_bm25:
            return False
        self.retriever = HybridRetriever(
            self.vector_store, self.bm25_store,
            self.graph_store, self.embedder, self.settings,
        )
        self._ingested = True
        logger.info("indexes_loaded")
        return True

    # ── Query ─────────────────────────────────────────────────────────────────

    def ask(self, query: str, session_id: str = "default") -> str:
        """Run the full RAG pipeline for one question. Returns answer string."""
        if not self._ingested or self.retriever is None:
            raise IndexNotFoundError("No index found. Run ingest first.")

        t_start = time.perf_counter()
        memory  = Memory(session_id, self.settings.memory_path)
        intent  = detect_intent(query)
        intent.raw_query = query

        search_query = reformulate(query, memory)
        intent.rewritten = search_query

        logger.info(
            "query_received",
            session_id=session_id,
            is_flow=intent.is_flow,
            is_security=intent.is_security,
        )

        candidates = self.retriever.retrieve(search_query)
        chunks     = self.reranker.rerank(
            search_query, candidates,
            self.settings.retrieval.rerank_top_k,
        )

        flow_narrative = self._run_flow_trace(intent, query)
        semgrep_str    = self._get_security_context(intent, chunks)

        system  = pick_system_prompt(intent.is_flow, intent.is_security, intent.is_multi_hop)
        context = build_context(
            chunks         = chunks,
            flow_narrative = flow_narrative,
            semgrep_str    = semgrep_str,
            memory_str     = memory.format_for_prompt(),
            limit          = self.settings.generation.context_limit,
        )
        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": f"{context}\n\n---\n\n## Question\n{query}"},
        ]

        answer = self.llm.generate(messages)
        memory.add("user",      query)
        memory.add("assistant", answer)

        elapsed = round(time.perf_counter() - t_start, 2)
        logger.info("query_complete", elapsed_s=elapsed)
        return answer

    def _run_flow_trace(self, intent: Intent, query: str) -> str:
        if not intent.is_flow or not intent.flow_symbol:
            return ""
        result = self.flow_tracer.run(intent.flow_symbol, query)
        if not result:
            return ""
        if "narrative" in result:
            return result["narrative"]
        if "error" in result:
            return f"Symbol `{intent.flow_symbol}` not found. Did you mean: {', '.join(result.get('suggestions', []))}"
        return ""

    def _get_security_context(self, intent: Intent, chunks: list) -> str:
        if not intent.is_security or not self.findings:
            return ""
        relevant = [
            f for f in self.findings
            if any(f.file == c["meta"].get("file", "") for c in chunks)
        ]
        return format_findings_for_prompt(relevant[:10])

    @property
    def is_ready(self) -> bool:
        return self._ingested and self.retriever is not None
