from __future__ import annotations

from pathlib import Path

from backend.runtime.factory import create_runtime_backend
from backend.runtime.mock_runtime import MockRuntime
from backend.runtime.pytorch_peft import PyTorchPeftRuntime


class _FakeAdapterModel:
    def __init__(self) -> None:
        self.active_adapter: str | None = None
        self.set_calls: list[str] = []

    def set_adapter(self, adapter_id: str) -> None:
        self.active_adapter = adapter_id
        self.set_calls.append(adapter_id)


def test_pytorch_peft_runtime_loads_adapter_once(tmp_path: Path) -> None:
    (tmp_path / "sql_postgres").mkdir()
    fake_model = object()
    fake_adapter_model = _FakeAdapterModel()
    load_calls: list[str] = []

    def base_model_loader() -> object:
        return fake_model

    def adapter_loader(model: object, adapter_path: Path, adapter_id: str) -> _FakeAdapterModel:
        assert model is fake_model
        load_calls.append(f"{adapter_path.name}:{adapter_id}")
        return fake_adapter_model

    runtime = PyTorchPeftRuntime(
        base_model_id="tiny-local-model",
        adapter_dir=tmp_path,
        device="cpu",
        eager_load=False,
        base_model_loader=base_model_loader,
        adapter_loader=adapter_loader,
    )

    first = runtime.activate_adapter("sql_postgres")
    second = runtime.activate_adapter("sql_postgres")

    assert first.loaded_from_disk is True
    assert second.loaded_from_disk is False
    assert len(load_calls) == 1
    assert fake_adapter_model.set_calls == ["sql_postgres", "sql_postgres"]


def test_factory_defaults_to_mock_runtime(monkeypatch) -> None:
    monkeypatch.delenv("LORA_JIT_RUNTIME_BACKEND", raising=False)
    backend = create_runtime_backend()
    assert isinstance(backend, MockRuntime)


def test_factory_falls_back_to_mock_when_pytorch_runtime_cannot_boot(monkeypatch, tmp_path: Path) -> None:
    missing_adapter_dir = tmp_path / "does-not-exist"
    monkeypatch.setenv("LORA_JIT_RUNTIME_BACKEND", "pytorch")
    monkeypatch.setenv("LORA_JIT_BASE_MODEL_ID", "tiny-local-model")
    monkeypatch.setenv("LORA_JIT_ADAPTER_DIR", str(missing_adapter_dir))
    monkeypatch.setenv("LORA_JIT_DEVICE", "cpu")
    monkeypatch.setenv("LORA_JIT_EAGER_LOAD", "false")

    backend = create_runtime_backend()
    assert isinstance(backend, MockRuntime)
