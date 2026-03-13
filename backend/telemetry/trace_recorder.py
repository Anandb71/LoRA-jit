from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from backend.contracts.schemas import TelemetryStreamEvent


class TraceRecorder:
    """Append-only NDJSON recorder for replay-grade telemetry traces."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = root_dir or Path("traces")
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def append_many(self, events: list[TelemetryStreamEvent]) -> int:
        grouped: dict[str, list[TelemetryStreamEvent]] = {}
        for event in events:
            grouped.setdefault(event.session_id, []).append(event)

        total = 0
        for session_id, session_events in grouped.items():
            trace_path = self.root_dir / f"{session_id}.ndjson"
            with trace_path.open("a", encoding="utf-8") as handle:
                for event in session_events:
                    row = {
                        "ingested_at": datetime.now(UTC).isoformat(),
                        "session_id": event.session_id,
                        "file_path": event.file_path,
                        "sequence_id": event.sequence_id,
                        "event": event.model_dump(mode="json"),
                    }
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                    total += 1
        return total

    def list_sessions(self) -> list[str]:
        return sorted(path.stem for path in self.root_dir.glob("*.ndjson"))

    def session_path(self, session_id: str) -> Path:
        return self.root_dir / f"{session_id}.ndjson"
