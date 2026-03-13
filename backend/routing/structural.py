from __future__ import annotations

from collections import Counter

from backend.contracts.schemas import RoutingDecision, TelemetryEvent


class StructuralRouter:
    """Deterministic structural baseline for MVP.

    This intentionally uses transparent heuristics before introducing learned models.
    """

    def __init__(self, fallback_adapter: str = "general") -> None:
        self._fallback_adapter = fallback_adapter

    def predict(self, event: TelemetryEvent) -> RoutingDecision:
        feature_tokens = [*event.symbols_in_scope]
        feature_tokens.extend(event.file_path.replace('\\', '/').split('/'))

        counts = Counter(token.lower() for token in feature_tokens if token)
        candidates = [name for name, _ in counts.most_common(3)]

        adapter_id = self._fallback_adapter
        reason = "fallback"
        confidence = 0.35

        if candidates:
            adapter_id = candidates[0]
            reason = "top structural token"
            confidence = 0.6

        return RoutingDecision(
            session_id=event.session_id,
            adapter_id=adapter_id,
            confidence=confidence,
            candidates=candidates,
            reason=reason,
        )
