from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from backend.contracts.schemas import TelemetryEvent, TelemetryStreamEvent


@dataclass(slots=True)
class ReconstructedPoint:
    timestamp: datetime
    event: TelemetryStreamEvent
    document_text: str


@dataclass(slots=True)
class SemanticWindow:
    session_id: str
    file_path: str
    symbol_path: list[str]
    start_timestamp: datetime
    end_timestamp: datetime
    start_sequence_id: int
    end_sequence_id: int
    event_count: int
    document_text: str


class StateReconstructor:
    """Replays NDJSON telemetry events into in-memory per-file document state."""

    def __init__(self) -> None:
        self._doc_state: dict[str, str] = {}

    @staticmethod
    def _line_start_offsets(text: str) -> list[int]:
        offsets = [0]
        for idx, ch in enumerate(text):
            if ch == "\n":
                offsets.append(idx + 1)
        return offsets

    @classmethod
    def _position_to_offset(cls, text: str, line: int, character: int) -> int:
        offsets = cls._line_start_offsets(text)
        if line >= len(offsets):
            return len(text)
        line_start = offsets[line]
        line_end = offsets[line + 1] if line + 1 < len(offsets) else len(text)
        return min(line_start + character, line_end)

    @classmethod
    def _apply_delta(
        cls,
        text: str,
        *,
        start_line: int,
        start_character: int,
        end_line: int,
        end_character: int,
        replacement: str,
    ) -> str:
        start = cls._position_to_offset(text, start_line, start_character)
        end = cls._position_to_offset(text, end_line, end_character)
        if end < start:
            end = start
        return f"{text[:start]}{replacement}{text[end:]}"

    def _apply_event(self, event: TelemetryStreamEvent) -> str:
        current = self._doc_state.get(event.file_path, "")

        if event.full_text is not None:
            current = event.full_text
        elif event.event_type == "text_change" and event.deltas:
            for delta in event.deltas:
                current = self._apply_delta(
                    current,
                    start_line=delta.range_start_line,
                    start_character=delta.range_start_character,
                    end_line=delta.range_end_line,
                    end_character=delta.range_end_character,
                    replacement=delta.text,
                )

        self._doc_state[event.file_path] = current
        return current

    def replay(self, events: list[TelemetryStreamEvent]) -> list[ReconstructedPoint]:
        points: list[ReconstructedPoint] = []
        for event in events:
            doc_text = self._apply_event(event)
            points.append(ReconstructedPoint(timestamp=event.created_at, event=event, document_text=doc_text))
        return points


class TraceCompiler:
    """Compiles NDJSON session telemetry into semantic windows and benchmark rows."""

    def __init__(self) -> None:
        self._reconstructor = StateReconstructor()

    def load_session_events(self, trace_path: Path) -> list[TelemetryStreamEvent]:
        events: list[TelemetryStreamEvent] = []
        with trace_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                events.append(TelemetryStreamEvent.model_validate(row["event"]))

        events.sort(key=lambda e: (e.created_at, e.sequence_id))
        return events

    def build_windows(self, events: list[TelemetryStreamEvent]) -> list[SemanticWindow]:
        points = self._reconstructor.replay(events)
        windows: list[SemanticWindow] = []

        current: SemanticWindow | None = None
        for point in points:
            symbol_path = point.event.symbol_path
            key_changed = (
                current is None
                or current.file_path != point.event.file_path
                or current.symbol_path != symbol_path
            )

            if key_changed:
                if current is not None:
                    windows.append(current)
                current = SemanticWindow(
                    session_id=point.event.session_id,
                    file_path=point.event.file_path,
                    symbol_path=list(symbol_path),
                    start_timestamp=point.timestamp,
                    end_timestamp=point.timestamp,
                    start_sequence_id=point.event.sequence_id,
                    end_sequence_id=point.event.sequence_id,
                    event_count=1,
                    document_text=point.document_text,
                )
                continue

            current.end_timestamp = point.timestamp
            current.end_sequence_id = point.event.sequence_id
            current.event_count += 1
            current.document_text = point.document_text

        if current is not None:
            windows.append(current)

        return windows

    @staticmethod
    def _derive_symbols(symbol_path: list[str]) -> list[str]:
        return [token for token in symbol_path if token]

    def to_unlabeled_benchmark_rows(self, windows: list[SemanticWindow]) -> list[dict]:
        rows: list[dict] = []
        for window in windows:
            cursor_line = 0
            cursor_column = 0

            event = TelemetryEvent(
                session_id=window.session_id,
                file_path=window.file_path,
                language_id=Path(window.file_path).suffix.lstrip('.') or "unknown",
                cursor_line=cursor_line,
                cursor_column=cursor_column,
                symbols_in_scope=self._derive_symbols(window.symbol_path),
                metadata={
                    "window_start": window.start_timestamp.isoformat(),
                    "window_end": window.end_timestamp.isoformat(),
                    "event_count": window.event_count,
                    "sequence_start": window.start_sequence_id,
                    "sequence_end": window.end_sequence_id,
                    "code_block": window.document_text,
                    "label_status": "pending_offline_annotation",
                },
            )

            rows.append(
                {
                    "event": event.model_dump(mode="json"),
                    "expected_adapter": "general",
                    "label_status": "pending_offline_annotation",
                }
            )
        return rows

    def compile_session(self, trace_path: Path) -> tuple[list[SemanticWindow], list[dict]]:
        events = self.load_session_events(trace_path)
        windows = self.build_windows(events)
        rows = self.to_unlabeled_benchmark_rows(windows)
        return windows, rows
