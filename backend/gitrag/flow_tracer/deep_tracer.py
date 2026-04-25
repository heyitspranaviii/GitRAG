from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from gitrag.core.types import CallNode, TraceFrame


class DeepTracer:
    def __init__(
        self,
        graph:                 nx.DiGraph,
        max_depth:             int  = 6,
        max_children_per_node: int  = 10,
        skip_externals:        bool = False,
    ) -> None:
        self.G            = graph
        self.max_depth    = max_depth
        self.max_children = max_children_per_node
        self.skip_ext     = skip_externals

    def trace(self, root_symbol: str) -> TraceFrame:
        return self._expand(root_symbol, depth=0, active_stack=set())

    def _expand(self, symbol: str, depth: int, active_stack: set) -> TraceFrame:
        if symbol not in self.G:
            stub = CallNode(
                symbol=symbol, file="<unknown>", start_line=0, end_line=0,
                language="", raw_body=f"# `{symbol}` not found in repo",
                is_external=True,
            )
            return TraceFrame(depth=depth, symbol=symbol, node=stub, is_external=True)

        node: CallNode = self.G.nodes[symbol]["data"]

        if symbol in active_stack:
            return TraceFrame(depth=depth, symbol=symbol, node=node, is_recursive_ref=True)

        if node.is_external and self.skip_ext:
            return TraceFrame(depth=depth, symbol=symbol, node=node, is_external=True)

        if depth >= self.max_depth:
            frame = TraceFrame(depth=depth, symbol=symbol, node=node)
            frame.children = [
                TraceFrame(
                    depth=depth + 1, symbol=c,
                    node=self.G.nodes[c]["data"] if c in self.G else CallNode(
                        symbol=c, file="<depth-limit>", start_line=0, end_line=0,
                        language="", raw_body="# depth limit reached", is_external=True,
                    ),
                    is_external=True,
                )
                for c in node.calls[:self.max_children]
            ]
            return frame

        active_stack.add(symbol)
        frame = TraceFrame(depth=depth, symbol=symbol, node=node)

        for callee in node.calls[:self.max_children]:
            frame.children.append(self._expand(callee, depth + 1, active_stack))

        active_stack.remove(symbol)
        return frame
