from __future__ import annotations

import re
from collections import Counter
from math import sqrt

from backend.contracts.schemas import RoutingDecision, TelemetryEvent

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _bag(tokens: list[str]) -> Counter[str]:
    return Counter(t for t in tokens if t)


def _cosine(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0

    dot = sum(a[token] * b[token] for token in a.keys() & b.keys())
    a_norm = sqrt(sum(v * v for v in a.values()))
    b_norm = sqrt(sum(v * v for v in b.values()))
    if a_norm == 0 or b_norm == 0:
        return 0.0
    return dot / (a_norm * b_norm)


class TextRouter:
    """Simple lexical-overlap baseline.

    Uses metadata query/prompt text when available plus structural context fields.
    """

    def __init__(self, adapter_catalog: list[str], fallback_adapter: str = "general") -> None:
        self._adapter_catalog = adapter_catalog or [fallback_adapter]
        self._fallback_adapter = fallback_adapter

    def predict(self, event: TelemetryEvent) -> RoutingDecision:
        query_text = str(event.metadata.get("query") or event.metadata.get("prompt") or "")
        event_text = " ".join(
            [
                event.file_path,
                event.language_id,
                query_text,
                " ".join(event.symbols_in_scope),
            ]
        )
        event_tokens = set(_tokenize(event_text))

        best_adapter = self._fallback_adapter
        best_score = 0.0

        scored: list[tuple[str, float]] = []
        for adapter in self._adapter_catalog:
            adapter_tokens = set(_tokenize(adapter.replace("-", " ").replace("_", " ")))
            if not adapter_tokens:
                score = 0.0
            else:
                score = len(event_tokens & adapter_tokens) / len(adapter_tokens)
            scored.append((adapter, score))
            if score > best_score:
                best_score = score
                best_adapter = adapter

        scored.sort(key=lambda x: x[1], reverse=True)
        candidates = [name for name, _ in scored[:3]]

        confidence = 0.35 if best_score == 0 else min(0.9, 0.45 + best_score)
        reason = "lexical overlap"
        if best_score == 0:
            reason = "text fallback"

        return RoutingDecision(
            session_id=event.session_id,
            adapter_id=best_adapter,
            confidence=confidence,
            candidates=candidates,
            reason=reason,
        )


class EmbeddingRouter:
    """Deterministic pseudo-embedding baseline using bag-of-token cosine similarity."""

    def __init__(self, adapter_catalog: list[str], fallback_adapter: str = "general") -> None:
        self._adapter_catalog = adapter_catalog or [fallback_adapter]
        self._fallback_adapter = fallback_adapter

    def predict(self, event: TelemetryEvent) -> RoutingDecision:
        query_text = str(event.metadata.get("query") or event.metadata.get("prompt") or "")
        event_text = " ".join(
            [event.file_path, event.language_id, " ".join(event.symbols_in_scope), query_text]
        )
        event_vec = _bag(_tokenize(event_text))

        best_adapter = self._fallback_adapter
        best_score = 0.0

        scored: list[tuple[str, float]] = []
        for adapter in self._adapter_catalog:
            adapter_vec = _bag(_tokenize(adapter.replace("-", " ").replace("_", " ")))
            score = _cosine(event_vec, adapter_vec)
            scored.append((adapter, score))
            if score > best_score:
                best_score = score
                best_adapter = adapter

        scored.sort(key=lambda x: x[1], reverse=True)
        candidates = [name for name, _ in scored[:3]]

        confidence = 0.35 if best_score == 0 else min(0.92, 0.5 + best_score)
        reason = "pseudo-embedding cosine"
        if best_score == 0:
            reason = "embedding fallback"

        return RoutingDecision(
            session_id=event.session_id,
            adapter_id=best_adapter,
            confidence=confidence,
            candidates=candidates,
            reason=reason,
        )
