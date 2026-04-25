from __future__ import annotations
import re
from gitrag.core.types import Intent, IntentType

FLOW_PATTERNS = [
    r"what happens (?:when|if) ['\"`]?([\w.]+)['\"`]? is called",
    r"what does ['\"`]?([\w.]+)['\"`]? do",
    r"trace ['\"`]?([\w.]+)['\"`]?",
    r"walk me through ['\"`]?([\w.]+)['\"`]?",
    r"explain ['\"`]?([\w.]+)['\"`]?\s*\(",
    r"execution (?:flow|path) of ['\"`]?([\w.]+)['\"`]?",
    r"call (?:chain|stack) (?:of|from) ['\"`]?([\w.]+)['\"`]?",
    r"how is ['\"`]?([\w.]+)['\"`]? (?:called|invoked|triggered)",
]
SECURITY_KEYWORDS = [
    "secure","security","vulnerab","injection","exploit","bug","safe",
    "dangerous","risk","attack","xss","sqli","csrf","overflow","sanitiz",
    "hardcod","secret","credential","password","token leak",
]
MULTI_HOP_KEYWORDS = [
    "from","to","through","across","pipeline","end to end","end-to-end",
    "how does a request","journey","path from","gets to","reaches",
]

def detect_intent(query: str) -> Intent:
    q = query.lower().strip()
    intent = Intent(raw_query=query)
    for pat in FLOW_PATTERNS:
        m = re.search(pat, q)
        if m:
            intent.is_flow = True
            intent.flow_symbol = m.group(1)
            intent.type = IntentType.FLOW
            break
    if any(kw in q for kw in SECURITY_KEYWORDS):
        intent.is_security = True
        if intent.type == IntentType.GENERAL:
            intent.type = IntentType.SECURITY
    if any(kw in q for kw in MULTI_HOP_KEYWORDS) and len(q.split()) > 8:
        intent.is_multi_hop = True
        if intent.type == IntentType.GENERAL:
            intent.type = IntentType.MULTI_HOP
    return intent
