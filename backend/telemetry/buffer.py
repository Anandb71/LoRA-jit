from __future__ import annotations

from collections import deque

from backend.contracts.schemas import TelemetryStreamEvent


class TelemetryBuffer:
    def __init__(self, capacity: int = 10_000) -> None:
        self._capacity = capacity
        self._events: deque[TelemetryStreamEvent] = deque(maxlen=capacity)

    def append_many(self, events: list[TelemetryStreamEvent]) -> int:
        for event in events:
            self._events.append(event)
        return len(events)

    def recent(self, limit: int = 100) -> list[TelemetryStreamEvent]:
        if limit <= 0:
            return []
        return list(self._events)[-limit:]

    def size(self) -> int:
        return len(self._events)
