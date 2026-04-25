from __future__ import annotations

from gitrag.core.logging import get_logger
from gitrag.core.types import Chunk
from gitrag.flow_tracer.call_graph import CallGraphBuilder
from gitrag.flow_tracer.deep_tracer import DeepTracer
from gitrag.flow_tracer.narrative import NarrativeAssembler
from gitrag.flow_tracer.resolver import SymbolResolver

logger = get_logger(__name__)


class FlowTracerOrchestrator:
    def __init__(self, settings) -> None:
        self.cfg       = settings.flow_tracer
        self.graph     = None
        self.tracer:   DeepTracer | None = None
        self.resolver: SymbolResolver | None = None
        self.assembler = NarrativeAssembler()

    def build(self, chunks: list[Chunk]) -> None:
        self.graph    = CallGraphBuilder().build(chunks)
        self.tracer   = DeepTracer(
            self.graph,
            max_depth             = self.cfg.max_depth,
            max_children_per_node = self.cfg.max_children,
            skip_externals        = self.cfg.skip_externals,
        )
        self.resolver = SymbolResolver(self.graph)
        logger.info("flow_tracer_ready")

    def run(self, symbol: str, query: str) -> dict | None:
        if not self.resolver:
            return None
        resolved = self.resolver.resolve(symbol)
        if not resolved:
            suggestions = self.resolver.suggest(symbol)
            logger.warning("symbol_not_found", symbol=symbol, suggestions=suggestions)
            return {"error": f"`{symbol}` not found", "suggestions": suggestions}
        frame     = self.tracer.trace(resolved)
        narrative = self.assembler.assemble(frame, query)
        summary   = self.assembler.summary(frame)
        logger.info("flow_trace_complete", symbol=resolved, summary_length=len(summary))
        return {"symbol": resolved, "narrative": narrative, "summary": summary}
