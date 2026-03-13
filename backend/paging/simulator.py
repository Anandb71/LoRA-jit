from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PagingStats:
    warm_hits: int = 0
    cold_misses: int = 0
    evictions: int = 0


class PagingSimulator:
    def __init__(self, max_hot_adapters: int = 2) -> None:
        self.max_hot_adapters = max_hot_adapters
        self._hot: list[str] = []
        self.stats = PagingStats()

    def touch(self, adapter_id: str) -> None:
        if adapter_id in self._hot:
            self.stats.warm_hits += 1
            self._hot.remove(adapter_id)
            self._hot.append(adapter_id)
            return

        self.stats.cold_misses += 1
        if len(self._hot) >= self.max_hot_adapters:
            self._hot.pop(0)
            self.stats.evictions += 1
        self._hot.append(adapter_id)

    def snapshot(self) -> list[str]:
        return list(self._hot)
