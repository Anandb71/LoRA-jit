from __future__ import annotations

import json
from pathlib import Path

from backend.training.peft_finetune import load_jsonl_dataset


def test_load_jsonl_dataset_filters_bad_rows(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    rows = [
        {"text": "hello world"},
        {"text": ""},
        {"instruction": "missing text"},
        {"text": "second"},
    ]
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")

    loaded = load_jsonl_dataset(path)
    assert [item["text"] for item in loaded] == ["hello world", "second"]


def test_load_jsonl_dataset_honors_max_samples(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for i in range(10):
            handle.write(json.dumps({"text": f"sample {i}"}) + "\n")

    loaded = load_jsonl_dataset(path, max_samples=3)
    assert len(loaded) == 3
