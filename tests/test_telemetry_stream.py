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
                "document_version": 1,
                "cursor_line": 10,
                "cursor_column": 2,
                "deltas": [],
                "metadata": {"source": "test"},
            },
            {
                "session_id": "s-1",
                "event_type": "text_change",
                "file_path": "src/app.py",
                "language_id": "python",
                "document_version": 2,
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

    recent_response = client.get("/telemetry/recent", params={"limit": 2})
    assert recent_response.status_code == 200
    recent = recent_response.json()
    assert len(recent) == 2
    assert recent[-1]["event_type"] == "text_change"
