from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class PagingStats:
    warm_hits: int = 0
    cold_misses: int = 0
    evictions: int = 0


@dataclass(slots=True)
class PagingTouchResult:
    paging_status: str
    evicted_adapters: list[str]
    warm_adapters: list[str]
    total_hot_mb: float


class PagingSimulator:
    def __init__(
        self,
        max_hot_adapters: int = 2,
        *,
        max_hot_mb: float | None = None,
        adapter_sizes_mb: dict[str, float] | None = None,
        default_adapter_size_mb: float = 128.0,
    ) -> None:
        self.max_hot_adapters = max_hot_adapters
        self.max_hot_mb = max_hot_mb
        self.default_adapter_size_mb = max(1.0, float(default_adapter_size_mb))
        self.adapter_sizes_mb = {k: max(1.0, float(v)) for k, v in (adapter_sizes_mb or {}).items()}
        self._hot: list[str] = []
        self.stats = PagingStats()

    def set_adapter_sizes_mb(self, sizes: dict[str, float]) -> None:
        self.adapter_sizes_mb = {k: max(1.0, float(v)) for k, v in sizes.items()}

    def _size_mb(self, adapter_id: str) -> float:
        return float(self.adapter_sizes_mb.get(adapter_id, self.default_adapter_size_mb))

    def _total_hot_mb(self) -> float:
        return sum(self._size_mb(adapter_id) for adapter_id in self._hot)

    def touch(self, adapter_id: str) -> PagingTouchResult:
        evicted: list[str] = []

        if adapter_id in self._hot:
            self.stats.warm_hits += 1
            self._hot.remove(adapter_id)
            self._hot.append(adapter_id)
            return PagingTouchResult(
                paging_status="warm_hit",
                evicted_adapters=evicted,
                warm_adapters=list(self._hot),
                total_hot_mb=self._total_hot_mb(),
            )

        self.stats.cold_misses += 1
        if len(self._hot) >= self.max_hot_adapters:
            evicted.append(self._hot.pop(0))
            self.stats.evictions += 1
        self._hot.append(adapter_id)

        if self.max_hot_mb is not None:
            while len(self._hot) > 1 and self._total_hot_mb() > self.max_hot_mb:
                evicted.append(self._hot.pop(0))
                self.stats.evictions += 1

        return PagingTouchResult(
            paging_status="cold_miss",
            evicted_adapters=evicted,
            warm_adapters=list(self._hot),
            total_hot_mb=self._total_hot_mb(),
        )

    def snapshot(self) -> list[str]:
        return list(self._hot)
