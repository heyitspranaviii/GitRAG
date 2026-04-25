from __future__ import annotations

import re

import networkx as nx

from gitrag.chunking.ast_chunker import LANG_REGISTRY, TS_CORE
from gitrag.core.logging import get_logger
from gitrag.core.types import CallNode, Chunk

logger = get_logger(__name__)

try:
    from tree_sitter import Language, Parser
except ImportError:
    pass


def _regex_extract_calls(code: str) -> list[str]:
    return list(set(re.findall(r"\b([a-zA-Z_]\w*)\s*\(", code)))


def _ts_extract_calls(code: str, language: str) -> list[str]:
    if not TS_CORE or language not in LANG_REGISTRY:
        return _regex_extract_calls(code)
    ts_module = LANG_REGISTRY[language][0]
    if ts_module is None:
        return _regex_extract_calls(code)
    try:
        ts_lang = Language(ts_module.language())
        parser  = Parser(ts_lang)
        tree    = parser.parse(code.encode("utf-8"))
    except Exception:
        return _regex_extract_calls(code)
    calls: list[str] = []

    def walk(node) -> None:
        if node.type == "call":
            fn = node.child_by_field_name("function")
            if fn:
                text = code.encode("utf-8")[fn.start_byte:fn.end_byte].decode("utf-8", "ignore")
                name = text.split(".")[-1].strip()
                if name and name.isidentifier():
                    calls.append(name)
        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return list(set(calls))


class CallGraphBuilder:
    def build(self, chunks: list[Chunk]) -> nx.DiGraph:
        G     = nx.DiGraph()
        known: set[str] = set()

        for c in chunks:
            G.add_node(c.symbol_name, data=CallNode(
                symbol     = c.symbol_name,
                file       = c.file,
                start_line = c.start_line,
                end_line   = c.end_line,
                language   = c.language,
                raw_body   = c.raw_text,
                docstring  = c.docstring,
            ))
            known.add(c.symbol_name)

        for c in chunks:
            callees = _ts_extract_calls(c.raw_text, c.language)
            G.nodes[c.symbol_name]["data"].calls = callees
            for callee in callees:
                if callee not in known:
                    G.add_node(callee, data=CallNode(
                        symbol=callee, file="<external>",
                        start_line=0, end_line=0, language=c.language,
                        raw_body=f"# External: {callee}",
                        is_external=True,
                    ))
                    known.add(callee)
                G.add_edge(c.symbol_name, callee)

        logger.info("call_graph_built", nodes=G.number_of_nodes(), edges=G.number_of_edges())
        return G
