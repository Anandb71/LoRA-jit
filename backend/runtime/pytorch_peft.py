from __future__ import annotations

import importlib
import os
import time
from pathlib import Path
from typing import Any, Callable

from backend.runtime.interface import ActivationResult, AdapterState, RuntimeBackend
from backend.training.adapter_artifacts import AdapterArtifactError, validate_adapter_directory


BaseModelLoader = Callable[[], Any]
AdapterLoader = Callable[[Any, Path, str], Any]


class PyTorchPeftRuntime(RuntimeBackend):
    """Local PEFT runtime for small-model adapter hot-swapping.

    Design goals:
    - can be instantiated on a normal dev machine
    - imports heavy ML dependencies lazily
    - supports fake loaders in tests so CI does not need torch/peft
    - measures the real wall-clock time spent loading/switching adapters
    """

    def __init__(
        self,
        *,
        base_model_id: str,
        adapter_dir: str | Path,
        device: str = "cpu",
        eager_load: bool = False,
        base_model_loader: BaseModelLoader | None = None,
        adapter_loader: AdapterLoader | None = None,
    ) -> None:
        self._base_model_id = base_model_id
        self._adapter_dir = Path(adapter_dir)
        self._device = device
        self._base_model_loader = base_model_loader
        self._adapter_loader = adapter_loader

        self._base_model: Any | None = None
        self._tokenizer: Any | None = None
        self._adapter_model: Any | None = None
        self._loaded_adapters: set[str] = set()
        self._active_adapter: str | None = None

        if not self._adapter_dir.exists():
            raise FileNotFoundError(f"Adapter directory not found: {self._adapter_dir}")

        if eager_load:
            self._ensure_base_model_loaded()

    @property
    def backend_name(self) -> str:
        return "pytorch-peft"

    @property
    def active_adapter_id(self) -> str | None:
        return self._active_adapter

    def list_adapters(self) -> list[str]:
        if self._adapter_loader is not None:
            return sorted(path.name for path in self._adapter_dir.iterdir() if path.is_dir())

        adapters: list[str] = []
        for path in self._adapter_dir.iterdir():
            if not path.is_dir():
                continue
            try:
                validate_adapter_directory(path)
                adapters.append(path.name)
            except AdapterArtifactError:
                continue
        return sorted(adapters)

    def preload_adapter(self, adapter_id: str) -> None:
        if adapter_id not in self.list_adapters():
            raise ValueError(f"Unknown adapter: {adapter_id}")
        if adapter_id in self._loaded_adapters:
            return
        self._load_adapter(adapter_id)

    def activate_adapter(self, adapter_id: str) -> ActivationResult:
        if adapter_id not in self.list_adapters():
            raise ValueError(f"Unknown adapter: {adapter_id}")

        loaded_from_disk = adapter_id not in self._loaded_adapters
        started = time.perf_counter()

        if loaded_from_disk:
            self._load_adapter(adapter_id)

        if self._adapter_model is not None and hasattr(self._adapter_model, "set_adapter"):
            self._adapter_model.set_adapter(adapter_id)
        self._active_adapter = adapter_id

        activation_latency_ms = (time.perf_counter() - started) * 1000
        return ActivationResult(
            state=AdapterState(adapter_id=adapter_id, warm=True, active=True),
            activation_latency_ms=activation_latency_ms,
            loaded_from_disk=loaded_from_disk,
        )

    def generate(self, prompt: str, max_tokens: int) -> str:
        max_new_tokens = max(1, int(max_tokens))
        model = self._adapter_model or self._ensure_base_model_loaded()
        tokenizer = self._ensure_tokenizer_loaded()

        try:
            torch = importlib.import_module("torch")
            model.eval()

            if self._active_adapter and hasattr(model, "set_adapter"):
                model.set_adapter(self._active_adapter)

            encoded = tokenizer(prompt, return_tensors="pt")
            try:
                model_device = next(model.parameters()).device
                encoded = {key: value.to(model_device) for key, value in encoded.items()}
            except Exception:  # noqa: BLE001
                pass

            with torch.no_grad():
                output_ids = model.generate(
                    **encoded,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    pad_token_id=tokenizer.eos_token_id,
                )

            input_len = int(encoded["input_ids"].shape[1])
            generated_ids = output_ids[0][input_len:]
            text = tokenizer.decode(generated_ids, skip_special_tokens=True)
            return text if text else "\n"
        except Exception:  # noqa: BLE001
            return "\n    # generation unavailable"

    def _load_adapter(self, adapter_id: str) -> None:
        model = self._ensure_base_model_loaded()
        adapter_path = self._adapter_dir / adapter_id

        if self._adapter_loader is None:
            validate_adapter_directory(adapter_path)

        if self._adapter_loader is not None:
            self._adapter_model = self._adapter_loader(model, adapter_path, adapter_id)
            self._loaded_adapters.add(adapter_id)
            return

        self._adapter_model = self._default_adapter_loader(model, adapter_path, adapter_id)
        self._loaded_adapters.add(adapter_id)

    def _ensure_base_model_loaded(self) -> Any:
        if self._base_model is not None:
            return self._base_model

        if self._base_model_loader is not None:
            self._base_model = self._base_model_loader()
            return self._base_model

        try:
            transformers = importlib.import_module("transformers")
        except ImportError as exc:  # pragma: no cover - exercised via factory fallback
            raise RuntimeError(
                "transformers is required for PyTorchPeftRuntime. Install LoRA-JIT with the runtime extras."
            ) from exc

        auto_model_cls = getattr(transformers, "AutoModelForCausalLM")

        model_kwargs: dict[str, Any] = {"device_map": self._device}
        if self._device == "cpu":
            model_kwargs.pop("device_map", None)

        self._base_model = auto_model_cls.from_pretrained(self._base_model_id, **model_kwargs)
        return self._base_model

    def _ensure_tokenizer_loaded(self) -> Any:
        if self._tokenizer is not None:
            return self._tokenizer

        try:
            transformers = importlib.import_module("transformers")
        except ImportError as exc:  # pragma: no cover - exercised via factory fallback
            raise RuntimeError(
                "transformers is required for PyTorchPeftRuntime. Install LoRA-JIT with the runtime extras."
            ) from exc

        auto_tokenizer_cls = getattr(transformers, "AutoTokenizer")
        self._tokenizer = auto_tokenizer_cls.from_pretrained(self._base_model_id, use_fast=True)
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
        return self._tokenizer

    def _default_adapter_loader(self, model: Any, adapter_path: Path, adapter_id: str) -> Any:
        try:
            peft_module = importlib.import_module("peft")
        except ImportError as exc:  # pragma: no cover - exercised via factory fallback
            raise RuntimeError(
                "peft is required for PyTorchPeftRuntime. Install LoRA-JIT with the runtime extras."
            ) from exc

        peft_model_cls = getattr(peft_module, "PeftModel")

        if self._adapter_model is None:
            return peft_model_cls.from_pretrained(model, str(adapter_path), adapter_name=adapter_id)

        self._adapter_model.load_adapter(str(adapter_path), adapter_name=adapter_id)
        return self._adapter_model


def runtime_config_from_env() -> dict[str, str | bool]:
    preload_raw = os.environ.get("LORA_JIT_PRELOAD_ADAPTERS", "")
    preload_adapters = [
        part.strip()
        for part in preload_raw.split(",")
        if part.strip()
    ]

    return {
        "backend": os.environ.get("LORA_JIT_RUNTIME_BACKEND", "mock").strip().lower(),
        "base_model_id": os.environ.get("LORA_JIT_BASE_MODEL_ID", "Qwen/Qwen1.5-0.5B"),
        "adapter_dir": os.environ.get("LORA_JIT_ADAPTER_DIR", "adapters"),
        "device": os.environ.get("LORA_JIT_DEVICE", "cpu"),
        "eager_load": os.environ.get("LORA_JIT_EAGER_LOAD", "false").strip().lower() == "true",
        "preload_adapters": preload_adapters,
    }
