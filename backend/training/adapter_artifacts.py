from __future__ import annotations

from pathlib import Path


REQUIRED_ADAPTER_FILES = (
    "adapter_config.json",
    "adapter_model.safetensors",
)


class AdapterArtifactError(ValueError):
    pass


def validate_adapter_directory(adapter_path: str | Path) -> Path:
    path = Path(adapter_path)
    if not path.exists() or not path.is_dir():
        raise AdapterArtifactError(f"Adapter directory not found: {path}")

    missing = [name for name in REQUIRED_ADAPTER_FILES if not (path / name).exists()]
    if missing:
        raise AdapterArtifactError(
            f"Adapter directory {path} is missing required files: {missing}"
        )

    return path
