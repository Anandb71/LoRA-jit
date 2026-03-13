import json

import pytest

from backend.labeling.auto_labeler import (
    HeuristicLabelProvider,
    annotate_compiled_rows,
    parse_structured_label,
)


def test_parse_structured_label_rejects_unknown_adapter() -> None:
    raw = json.dumps(
        {
            "primary_adapter": "unknown_adapter",
            "acceptable_alternatives": ["python_core"],
            "confidence": 0.9,
            "reasoning": "test",
        }
    )

    with pytest.raises(ValueError):
        parse_structured_label(raw)


def test_annotate_compiled_rows_adds_expected_label() -> None:
    rows = [
        {
            "event": {
                "session_id": "s1",
                "file_path": "src/query.py",
                "language_id": "py",
                "cursor_line": 0,
                "cursor_column": 0,
                "symbols_in_scope": ["query_db"],
                "metadata": {
                    "code_block": "SELECT * FROM users WHERE id = $1",
                    "label_status": "pending_offline_annotation",
                },
            },
            "expected_adapter": "general",
            "label_status": "pending_offline_annotation",
        }
    ]

    annotated = annotate_compiled_rows(rows, provider=HeuristicLabelProvider())
    assert len(annotated) == 1
    assert annotated[0]["label_status"] == "auto_labeled"
    assert "expected_label" in annotated[0]
    assert annotated[0]["expected_label"]["primary_adapter"] in {
        "sql_postgres",
        "python_core",
        "data_engineering_general",
        "general",
    }
