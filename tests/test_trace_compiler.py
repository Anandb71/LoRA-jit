import json
from pathlib import Path

from backend.benchmark.trace_compiler import TraceCompiler


def _write_ndjson(path: Path, rows: list[dict]) -> None:
    text = "\n".join(json.dumps(row) for row in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def test_trace_compiler_reconstructs_text_and_windows(tmp_path: Path) -> None:
    trace_path = tmp_path / "session.ndjson"
    rows = [
        {
            "event": {
                "session_id": "s1",
                "event_type": "heartbeat",
                "file_path": "src/app.py",
                "language_id": "python",
                "sequence_id": 1,
                "document_version": 1,
                "full_text": "def auth():\n    pass\n",
                "symbol_path": ["auth"],
                "deltas": [],
                "metadata": {},
                "created_at": "2026-03-13T10:00:00+00:00",
            }
        },
        {
            "event": {
                "session_id": "s1",
                "event_type": "text_change",
                "file_path": "src/app.py",
                "language_id": "python",
                "sequence_id": 2,
                "document_version": 2,
                "symbol_path": ["auth"],
                "deltas": [
                    {
                        "range_start_line": 1,
                        "range_start_character": 4,
                        "range_end_line": 1,
                        "range_end_character": 8,
                        "text": "return True",
                    }
                ],
                "metadata": {},
                "created_at": "2026-03-13T10:00:01+00:00",
            }
        },
        {
            "event": {
                "session_id": "s1",
                "event_type": "cursor",
                "file_path": "src/app.py",
                "language_id": "python",
                "sequence_id": 3,
                "document_version": 2,
                "cursor_line": 3,
                "cursor_column": 1,
                "symbol_path": ["query_db"],
                "deltas": [],
                "metadata": {},
                "created_at": "2026-03-13T10:00:02+00:00",
            }
        },
    ]
    _write_ndjson(trace_path, rows)

    compiler = TraceCompiler()
    windows, benchmark_rows = compiler.compile_session(trace_path)

    assert len(windows) == 2
    assert windows[0].symbol_path == ["auth"]
    assert "return True" in windows[0].document_text
    assert windows[1].symbol_path == ["query_db"]

    assert len(benchmark_rows) == 2
    assert benchmark_rows[0]["label_status"] == "pending_offline_annotation"
    assert benchmark_rows[0]["event"]["metadata"]["label_status"] == "pending_offline_annotation"
