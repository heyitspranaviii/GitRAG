from __future__ import annotations
from gitrag.memory.conversation import Memory

REFERENCE_SIGNALS = [
    " it "," its "," this "," that "," they "," them ",
    " the function"," the class"," the method"," the same",
    " above"," previous"," mentioned","what about","how about",
]

def reformulate(query: str, memory: Memory) -> str:
    history = memory.get_history(last_n=4)
    if not history: return query
    q_lower = " " + query.lower() + " "
    needs_rewrite = any(sig in q_lower for sig in REFERENCE_SIGNALS) or len(query.split()) <= 4
    if not needs_rewrite: return query
    last_user = next((t.content for t in reversed(history) if t.role=="user" and t.content!=query), None)
    if last_user:
        return f"{query} (in the context of: {last_user[:120]})"
    return query
