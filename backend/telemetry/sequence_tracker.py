from __future__ import annotations

from collections import defaultdict

from backend.contracts.schemas import TelemetryStreamEvent


class SequenceTracker:
    """Tracks per-session/per-file sequence continuity and signals gaps."""

    def __init__(self) -> None:
        self._last_sequence: dict[tuple[str, str], int] = {}
        self._resync_needed: defaultdict[str, set[str]] = defaultdict(set)

    def observe(self, event: TelemetryStreamEvent) -> bool:
        key = (event.session_id, event.file_path)
        last = self._last_sequence.get(key)
        self._last_sequence[key] = max(event.sequence_id, last or 0)

        if last is None:
            return False

        if event.sequence_id == last + 1:
            return False

        self._resync_needed[event.session_id].add(event.file_path)
        return True

    def acknowledge_heartbeat(self, event: TelemetryStreamEvent) -> None:
        if event.event_type != "heartbeat":
            return
        files = self._resync_needed.get(event.session_id)
        if not files:
            return
        files.discard(event.file_path)

    def pending_resync_files(self, session_id: str) -> list[str]:
        return sorted(self._resync_needed.get(session_id, set()))
