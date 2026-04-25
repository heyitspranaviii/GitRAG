from __future__ import annotations

def _key(item: dict) -> str:
    if "chunk_id" in item: return item["chunk_id"]
    m = item.get("meta", {})
    return m.get("symbol","") + "::" + m.get("file","")

def rrf(results_lists: list[list[dict]], k: int = 60) -> list[dict]:
    scores: dict[str, float] = {}
    items:  dict[str, dict]  = {}
    for results in results_lists:
        for rank, item in enumerate(results):
            key = _key(item)
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank + 1)
            items[key]  = item
    return [items[k] for k in sorted(scores, key=lambda x: scores[x], reverse=True)]
