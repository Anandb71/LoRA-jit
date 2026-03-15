from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class AdapterState:
    adapter_id: str
    warm: bool
    active: bool


@dataclass(slots=True)
class ActivationResult:
    state: AdapterState
    activation_latency_ms: float
    loaded_from_disk: bool


class RuntimeBackend(ABC):
    @property
    @abstractmethod
    def backend_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def active_adapter_id(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    def list_adapters(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def preload_adapter(self, adapter_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def activate_adapter(self, adapter_id: str) -> ActivationResult:
        raise NotImplementedError

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int) -> str:
        raise NotImplementedError
