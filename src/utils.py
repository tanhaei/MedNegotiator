from __future__ import annotations

import json
import math
import re
from typing import Any, Dict, Iterable, List


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def extract_json_object(text: str) -> Dict[str, Any]:
    """Best-effort JSON extraction from plain or markdown-wrapped responses."""
    text = text.strip()
    if not text:
        return {}

    # Direct parse first
    try:
        parsed = json.loads(text)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        pass

    # Markdown code fences
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        try:
            parsed = json.loads(fenced.group(1))
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            pass

    # First balanced object
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z0-9_\-]+", text.lower())


def cosine_token_similarity(text_a: str, text_b: str) -> float:
    """A lightweight semantic anchoring proxy without external embedding services."""
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)
    if not tokens_a or not tokens_b:
        return 0.0

    freq_a: Dict[str, int] = {}
    freq_b: Dict[str, int] = {}
    for token in tokens_a:
        freq_a[token] = freq_a.get(token, 0) + 1
    for token in tokens_b:
        freq_b[token] = freq_b.get(token, 0) + 1

    shared = set(freq_a).intersection(freq_b)
    numerator = sum(freq_a[token] * freq_b[token] for token in shared)
    norm_a = math.sqrt(sum(value * value for value in freq_a.values()))
    norm_b = math.sqrt(sum(value * value for value in freq_b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)


def unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered
