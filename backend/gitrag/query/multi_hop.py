from __future__ import annotations
from gitrag.index.graph_store import GraphStore

def expand_multi_hop(initial_chunks: list[dict], graph: GraphStore, hops: int = 2) -> list[str]:
    extra_ids: list[str] = []
    seen: set[str] = set()
    for chunk in initial_chunks:
        fpath = chunk["meta"].get("file","")
        if not fpath or fpath in seen: continue
        seen.add(fpath)
        extra_ids.extend(graph.neighbors(fpath, hops=hops))
    seen2: set[str] = set()
    return [cid for cid in extra_ids if not (cid in seen2 or seen2.add(cid))]
