from __future__ import annotations

import math

from gitrag.core.types import EvalResult


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if k == 0:
        return 0.0
    hits = sum(1 for r in retrieved_ids[:k] if r in relevant_ids)
    return hits / k


def mean_reciprocal_rank(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    for rank, rid in enumerate(retrieved_ids, start=1):
        if rid in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    def dcg(ids: list[str]) -> float:
        return sum(
            1.0 / math.log2(rank + 1)
            for rank, rid in enumerate(ids[:k], start=1)
            if rid in relevant_ids
        )
    actual = dcg(retrieved_ids)
    ideal  = dcg(list(relevant_ids)[:k] + [""] * k)
    return actual / ideal if ideal > 0 else 0.0


def faithfulness_score(answer: str, context_chunks: list[dict]) -> float:
    context_tokens: set[str] = set()
    for chunk in context_chunks:
        context_tokens.update(chunk.get("text", "").lower().split())
    if not context_tokens:
        return 0.0
    sentences = [s.strip() for s in answer.replace("\n", ". ").split(".") if s.strip()]
    if not sentences:
        return 0.0
    grounded = sum(
        1 for s in sentences
        if any(tok in context_tokens for tok in s.lower().split() if len(tok) > 3)
    )
    return round(grounded / len(sentences), 3)


def evaluate(
    retrieved_ids:  list[str],
    relevant_ids:   set[str],
    answer:         str,
    context_chunks: list[dict],
    k:              int = 5,
) -> EvalResult:
    return EvalResult(
        precision_at_k = round(precision_at_k(retrieved_ids, relevant_ids, k), 3),
        mrr            = round(mean_reciprocal_rank(retrieved_ids, relevant_ids), 3),
        ndcg           = round(ndcg_at_k(retrieved_ids, relevant_ids, k), 3),
        faithfulness   = faithfulness_score(answer, context_chunks),
    )
