from __future__ import annotations

from backend.runtime.interface import AdapterState, RuntimeBackend


class MockRuntime(RuntimeBackend):
    def __init__(self, adapters: list[str] | None = None) -> None:
        self._adapters = adapters or ["general", "python", "typescript"]
        self._warm: set[str] = set()

    def list_adapters(self) -> list[str]:
        return list(self._adapters)

    def preload_adapter(self, adapter_id: str) -> None:
        if adapter_id in self._adapters:
            self._warm.add(adapter_id)

    def activate_adapter(self, adapter_id: str) -> AdapterState:
        self.preload_adapter(adapter_id)
        return AdapterState(adapter_id=adapter_id, warm=True, active=True)
