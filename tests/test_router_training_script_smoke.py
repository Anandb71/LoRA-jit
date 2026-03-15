from __future__ import annotations

from pathlib import Path

from backend.training.router_trainer import LearnedRouterTrainer


def test_trainer_load_rows_multiple_files(tmp_path: Path) -> None:
    a = tmp_path / "a.json"
    b = tmp_path / "b.json"
    payload = "[{\"event\": {\"session_id\": \"s\", \"file_path\": \"README.md\", \"language_id\": \"markdown\", \"cursor_line\": 0, \"cursor_column\": 0, \"symbols_in_scope\": [], \"metadata\": {\"code_block\": \"hello\"}}, \"expected_adapter\": \"general\"}]"
    a.write_text(payload, encoding="utf-8")
    b.write_text(payload, encoding="utf-8")

    trainer = LearnedRouterTrainer()
    rows = trainer.load_rows([a, b])
    assert len(rows) == 2
