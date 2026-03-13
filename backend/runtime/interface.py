from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class AdapterState:
    adapter_id: str
    warm: bool
    active: bool


class RuntimeBackend(ABC):
    @abstractmethod
    def list_adapters(self) -> list[str]:
        raise NotImplementedError

    @abstractmethod
    def preload_adapter(self, adapter_id: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def activate_adapter(self, adapter_id: str) -> AdapterState:
        raise NotImplementedError
