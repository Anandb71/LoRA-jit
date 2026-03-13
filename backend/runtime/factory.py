from __future__ import annotations

import logging
from pathlib import Path

from backend.labeling.ontology import list_adapter_ids
from backend.runtime.interface import RuntimeBackend
from backend.runtime.mock_runtime import MockRuntime
from backend.runtime.pytorch_peft import PyTorchPeftRuntime, runtime_config_from_env

logger = logging.getLogger(__name__)


def create_runtime_backend() -> RuntimeBackend:
    """Create the configured runtime backend.

    Default behavior is conservative: use the mock runtime unless the user
    explicitly sets `LORA_JIT_RUNTIME_BACKEND=pytorch`.
    If the PyTorch runtime cannot be created, fall back to mock and log why.
    """
    config = runtime_config_from_env()
    backend = str(config["backend"])

    if backend != "pytorch":
        return MockRuntime(adapters=list_adapter_ids())

    try:
        return PyTorchPeftRuntime(
            base_model_id=str(config["base_model_id"]),
            adapter_dir=Path(str(config["adapter_dir"])),
            device=str(config["device"]),
            eager_load=bool(config["eager_load"]),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Falling back to MockRuntime because PyTorchPeftRuntime failed to initialize: %s: %s",
            type(exc).__name__,
            exc,
        )
        return MockRuntime(adapters=list_adapter_ids())
