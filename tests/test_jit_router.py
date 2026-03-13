from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from backend.contracts.schemas import TelemetryStreamEvent
from backend.labeling.llm_provider import LlmLabelProvider
from backend.paging.simulator import PagingSimulator
from backend.routing.jit_router import JitRouter
from backend.routing.structural import StructuralRouter
from backend.runtime.mock_runtime import MockRuntime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_stream_event(
    session_id: str = "sess-test",
    file_path: str = "app/main.py",
    language_id: str = "python",
    symbol_path: list[str] | None = None,
    sequence_id: int = 1,
) -> TelemetryStreamEvent:
    return TelemetryStreamEvent(
        session_id=session_id,
        event_type="cursor",
        file_path=file_path,
        language_id=language_id,
        sequence_id=sequence_id,
        symbol_path=symbol_path or ["MyClass", "my_method"],
    )


# ---------------------------------------------------------------------------
# JitRouter tests
# ---------------------------------------------------------------------------

class TestJitRouter:
    def _make_router(self, adapters: list[str] | None = None) -> JitRouter:
        backend = MockRuntime(adapters=adapters or ["general", "python_core", "fastapi_service"])
        paging = PagingSimulator(max_hot_adapters=2)
        predictor = StructuralRouter(fallback_adapter="general")
        return JitRouter(backend=backend, paging=paging, predictor=predictor)

    def test_route_returns_jit_routing_decision(self):
        jit = self._make_router()
        event = _make_stream_event()
        decision = jit.route(event)

        assert decision.session_id == "sess-test"
        assert decision.adapter_id
        assert 0.0 <= decision.confidence <= 1.0
        assert decision.paging_status in ("warm_hit", "cold_miss")
        assert isinstance(decision.warm_adapters, list)
        assert decision.latency_prediction_ms >= 0.0
        assert decision.sequence_id == 1

    def test_first_call_is_always_cold_miss(self):
        jit = self._make_router()
        event = _make_stream_event()
        decision = jit.route(event)
        assert decision.paging_status == "cold_miss"

    def test_repeated_same_adapter_is_warm_hit(self):
        jit = self._make_router()
        event = _make_stream_event(symbol_path=["general"])
        # First call is a cold miss that populates the hot-set
        jit.route(event)
        # Second identical call should be a warm hit
        decision = jit.route(event)
        assert decision.paging_status == "warm_hit"

    def test_warm_adapters_snapshot_contains_activated_adapter(self):
        jit = self._make_router()
        event = _make_stream_event()
        decision = jit.route(event)
        assert decision.adapter_id in decision.warm_adapters

    def test_eviction_reduces_warm_set_to_max(self):
        backend = MockRuntime(adapters=["general", "a", "b", "c"])
        paging = PagingSimulator(max_hot_adapters=2)

        class _FixedPredictor:
            _adapters = ["a", "b", "c"]
            _idx = 0

            def predict(self, event):
                adapter = self._adapters[self._idx % len(self._adapters)]
                self._idx += 1
                from backend.contracts.schemas import RoutingDecision
                return RoutingDecision(
                    session_id=event.session_id,
                    adapter_id=adapter,
                    confidence=0.9,
                    candidates=[adapter],
                    reason="fixed",
                )

        jit = JitRouter(backend=backend, paging=paging, predictor=_FixedPredictor())
        for i in range(3):
            jit.route(_make_stream_event(sequence_id=i + 1))

        assert len(paging.snapshot()) <= 2

    def test_daemon_jit_route_endpoint(self):
        """Integration test: POST /jit/route via FastAPI TestClient."""
        from fastapi.testclient import TestClient
        from backend.daemon.app import app

        client = TestClient(app)
        payload = {
            "session_id": "d-sess",
            "event_type": "cursor",
            "file_path": "main.py",
            "language_id": "python",
            "sequence_id": 1,
            "symbol_path": ["MyRouter"],
        }
        resp = client.post("/jit/route", json=payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "adapter_id" in body
        assert "paging_status" in body
        assert "warm_adapters" in body
        assert "latency_prediction_ms" in body


# ---------------------------------------------------------------------------
# LlmLabelProvider tests
# ---------------------------------------------------------------------------

class TestLlmLabelProvider:
    def test_falls_back_to_heuristic_on_network_error(self):
        """When the HTTP call fails, should fall back to HeuristicLabelProvider."""
        provider = LlmLabelProvider(api_key="fake-key", fallback_on_error=True)

        with patch("backend.labeling.llm_provider.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
                Exception("connection refused")
            )
            label = provider.label(
                code_block="def fetch_users(): pass",
                symbols=["fetch_users"],
                metadata={"file_path": "api.py"},
            )

        assert label.primary_adapter  # heuristic should still return something
        assert 0.0 <= label.confidence <= 1.0

    def test_raises_when_fallback_disabled(self):
        provider = LlmLabelProvider(api_key="fake-key", fallback_on_error=False)

        with patch("backend.labeling.llm_provider.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.post.side_effect = (
                Exception("connection refused")
            )
            with pytest.raises(Exception, match="connection refused"):
                provider.label(code_block="x = 1", symbols=[], metadata={})

    def test_parses_valid_llm_response(self):
        """A well-formed LLM JSON response should be validated and returned."""
        provider = LlmLabelProvider(api_key="fake-key")

        llm_json = json.dumps({
            "primary_adapter": "python_core",
            "acceptable_alternatives": ["general"],
            "confidence": 0.88,
            "reasoning": "Pure Python function definitions.",
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": llm_json}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("backend.labeling.llm_provider.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response
            label = provider.label(
                code_block="def hello(): return 'world'",
                symbols=["hello"],
                metadata={},
            )

        assert label.primary_adapter == "python_core"
        assert "general" in label.acceptable_alternatives
        assert label.confidence == pytest.approx(0.88)

    def test_rejects_unknown_adapter_in_llm_response(self):
        """If the LLM hallucinates an adapter ID, parse_structured_label should raise."""
        provider = LlmLabelProvider(api_key="fake-key", fallback_on_error=False)

        bad_json = json.dumps({
            "primary_adapter": "invented_adapter_xyz",
            "acceptable_alternatives": [],
            "confidence": 0.9,
            "reasoning": "Hallucinated.",
        })
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": bad_json}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("backend.labeling.llm_provider.httpx.Client") as mock_client_cls:
            mock_client_cls.return_value.__enter__.return_value.post.return_value = mock_response
            with pytest.raises(ValueError, match="Unknown adapter_id"):
                provider.label(code_block="x = 1", symbols=[], metadata={})
