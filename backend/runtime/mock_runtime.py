from __future__ import annotations

import time

from backend.runtime.interface import ActivationResult, AdapterState, RuntimeBackend


class MockRuntime(RuntimeBackend):
    def __init__(
        self,
        adapters: list[str] | None = None,
        cold_load_latency_ms: float = 0.05,
        warm_switch_latency_ms: float = 0.0,
    ) -> None:
        self._adapters = adapters or ["general", "python", "typescript"]
        self._warm: set[str] = set()
        self._cold_load_latency_ms = max(0.0, cold_load_latency_ms)
        self._warm_switch_latency_ms = max(0.0, warm_switch_latency_ms)

    @property
    def backend_name(self) -> str:
        return "mock"

    def list_adapters(self) -> list[str]:
        return list(self._adapters)

    def preload_adapter(self, adapter_id: str) -> None:
        if adapter_id in self._adapters:
            self._warm.add(adapter_id)

    def activate_adapter(self, adapter_id: str) -> ActivationResult:
        warm_before = adapter_id in self._warm
        self.preload_adapter(adapter_id)

        simulated_ms = self._warm_switch_latency_ms if warm_before else self._cold_load_latency_ms
        started = time.perf_counter()
        if simulated_ms > 0:
            time.sleep(simulated_ms / 1000)
        measured_ms = (time.perf_counter() - started) * 1000

        return ActivationResult(
            state=AdapterState(adapter_id=adapter_id, warm=True, active=True),
            activation_latency_ms=measured_ms,
            loaded_from_disk=not warm_before,
        )
