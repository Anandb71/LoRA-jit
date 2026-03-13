from fastapi.testclient import TestClient

from backend.daemon.app import app


def test_telemetry_stream_accepts_batch_and_exposes_recent() -> None:
    client = TestClient(app)

    payload = {
        "events": [
            {
                "session_id": "s-1",
                "event_type": "cursor",
                "file_path": "src/app.py",
                "language_id": "python",
                "sequence_id": 1,
                "document_version": 1,
                "cursor_line": 10,
                "cursor_column": 2,
                "symbol_path": ["service", "query_db"],
                "deltas": [],
                "metadata": {"source": "test"},
            },
            {
                "session_id": "s-1",
                "event_type": "text_change",
                "file_path": "src/app.py",
                "language_id": "python",
                "sequence_id": 2,
                "document_version": 2,
                "symbol_path": [],
                "deltas": [
                    {
                        "range_start_line": 10,
                        "range_start_character": 2,
                        "range_end_line": 10,
                        "range_end_character": 2,
                        "text": "x",
                    }
                ],
                "metadata": {"source": "test"},
            },
        ]
    }

    stream_response = client.post("/telemetry/stream", json=payload)
    assert stream_response.status_code == 200
    body = stream_response.json()
    assert body["accepted"] == 2
    assert body["buffered_total"] >= 2
    assert body["sequence_gaps_detected"] == 0

    recent_response = client.get("/telemetry/recent", params={"limit": 2})
    assert recent_response.status_code == 200
    recent = recent_response.json()
    assert len(recent) == 2
    assert recent[-1]["event_type"] == "text_change"


def test_telemetry_stream_detects_gap_and_requests_resync() -> None:
    client = TestClient(app)

    payload = {
        "events": [
            {
                "session_id": "s-gap",
                "event_type": "text_change",
                "file_path": "src/main.py",
                "language_id": "python",
                "sequence_id": 1,
                "document_version": 1,
                "symbol_path": [],
                "deltas": [],
                "metadata": {"source": "test"},
            },
            {
                "session_id": "s-gap",
                "event_type": "text_change",
                "file_path": "src/main.py",
                "language_id": "python",
                "sequence_id": 3,
                "document_version": 3,
                "symbol_path": [],
                "deltas": [],
                "metadata": {"source": "test"},
            },
        ]
    }

    response = client.post("/telemetry/stream", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["sequence_gaps_detected"] >= 1
    assert "src/main.py" in body["resync_files"]


def test_trace_sessions_endpoint_lists_session_ids() -> None:
    client = TestClient(app)

    payload = {
        "events": [
            {
                "session_id": "s-trace",
                "event_type": "heartbeat",
                "file_path": "src/x.py",
                "language_id": "python",
                "sequence_id": 1,
                "document_version": 1,
                "full_text": "print('x')",
                "symbol_path": [],
                "deltas": [],
                "metadata": {"source": "test"},
            }
        ]
    }

    stream_response = client.post("/telemetry/stream", json=payload)
    assert stream_response.status_code == 200

    sessions_response = client.get("/trace/sessions")
    assert sessions_response.status_code == 200
    sessions = sessions_response.json()
    assert "s-trace" in sessions
