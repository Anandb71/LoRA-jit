from __future__ import annotations

from pathlib import Path

import pytest

from backend.training.adapter_artifacts import AdapterArtifactError, validate_adapter_directory


def test_validate_adapter_directory_accepts_required_files(tmp_path: Path) -> None:
    adapter_dir = tmp_path / "sql_postgres"
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "adapter_config.json").write_text("{}", encoding="utf-8")
    (adapter_dir / "adapter_model.safetensors").write_text("fake", encoding="utf-8")

    out = validate_adapter_directory(adapter_dir)
    assert out == adapter_dir


def test_validate_adapter_directory_raises_on_missing_files(tmp_path: Path) -> None:
    adapter_dir = tmp_path / "sql_postgres"
    adapter_dir.mkdir(parents=True)
    (adapter_dir / "adapter_config.json").write_text("{}", encoding="utf-8")

    with pytest.raises(AdapterArtifactError):
        validate_adapter_directory(adapter_dir)
