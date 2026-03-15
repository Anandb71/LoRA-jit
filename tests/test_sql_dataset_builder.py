from __future__ import annotations

from pathlib import Path

from backend.training.sql_dataset import generate_sql_postgres_examples, write_jsonl


def test_generate_sql_postgres_examples_size_and_schema() -> None:
    rows = generate_sql_postgres_examples(size=32, seed=7)
    assert len(rows) == 32
    for row in rows:
        assert row["domain"] == "sql_postgres"
        assert row["instruction"]
        assert row["input"]
        assert row["response"]
        assert "<|assistant|>" in row["text"]


def test_write_jsonl_round_trip_line_count(tmp_path: Path) -> None:
    rows = generate_sql_postgres_examples(size=11, seed=3)
    out = write_jsonl(rows, tmp_path / "train.jsonl")
    line_count = len(out.read_text(encoding="utf-8").splitlines())
    assert line_count == 11
