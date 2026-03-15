from __future__ import annotations

import time
from typing import Protocol

from backend.contracts.schemas import JitRoutingDecision, RoutingDecision, TelemetryEvent, TelemetryStreamEvent
from backend.paging.simulator import PagingSimulator
from backend.runtime.interface import RuntimeBackend


class Predictor(Protocol):
    """Structural duck-type for any router that can predict from a TelemetryEvent."""

    def predict(self, event: TelemetryEvent) -> RoutingDecision:
        ...


class JitRouter:
    """Closed-loop JIT adapter orchestrator.

    Wires the predict → page → activate pipeline into a single call.
    Each call to ``route()`` returns an enriched ``JitRoutingDecision`` that
    includes the base prediction, the paging status (warm hit vs. cold miss),
    the current hot-set snapshot, and the wall-clock prediction latency.
    """

    def __init__(
        self,
        backend: RuntimeBackend,
        paging: PagingSimulator,
        predictor: Predictor,
    ) -> None:
        self._backend = backend
        self._paging = paging
        self._predictor = predictor

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def route(self, event: TelemetryStreamEvent) -> JitRoutingDecision:
        """Run the full JIT inference loop for a single stream event.

        Steps
        -----
        1. Bridge ``TelemetryStreamEvent`` → ``TelemetryEvent`` for router
           compatibility (the routers were designed against the leaner schema).
        2. Time the base prediction.
        3. Update the paging simulator and determine hit/miss.
        4. Activate the chosen adapter in the runtime backend.
        5. Return the enriched decision.
        """
        te = self._bridge(event)

        start = time.perf_counter()
        decision = self._predictor.predict(te)
        latency_prediction_ms = (time.perf_counter() - start) * 1000

        paging = self._paging.touch(decision.adapter_id)

        activation = self._backend.activate_adapter(decision.adapter_id)
        latency_total_ms = latency_prediction_ms + activation.activation_latency_ms

        return JitRoutingDecision(
            session_id=decision.session_id,
            adapter_id=decision.adapter_id,
            confidence=decision.confidence,
            candidates=list(decision.candidates),
            reason=decision.reason,
            paging_status=paging.paging_status,
            warm_adapters=paging.warm_adapters,
            evicted_adapters=paging.evicted_adapters,
            total_hot_mb=paging.total_hot_mb,
            latency_prediction_ms=latency_prediction_ms,
            activation_latency_ms=activation.activation_latency_ms,
            latency_total_ms=latency_total_ms,
            runtime_backend=self._backend.backend_name,
            sequence_id=event.sequence_id,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _bridge(event: TelemetryStreamEvent) -> TelemetryEvent:
        """Convert a stream event to the compact TelemetryEvent shape."""
        return TelemetryEvent(
            session_id=event.session_id,
            file_path=event.file_path,
            language_id=event.language_id,
            cursor_line=event.cursor_line or 0,
            cursor_column=event.cursor_column or 0,
            symbols_in_scope=list(event.symbol_path),
            metadata=dict(event.metadata),
        )
