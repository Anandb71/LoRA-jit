from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from backend.training.adapter_artifacts import validate_adapter_directory


@dataclass(slots=True)
class FineTuneConfig:
    base_model_id: str
    dataset_path: Path
    adapter_output_dir: Path
    max_samples: int = 1000
    max_seq_len: int = 512
    batch_size: int = 2
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    num_train_epochs: float = 1.0
    warmup_ratio: float = 0.05
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    logging_steps: int = 10
    save_steps: int = 100


def _lazy_import_ml_modules() -> tuple[Any, Any, Any, Any, Any, Any, Any]:
    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        default_data_collator,
    )

    return (
        torch,
        LoraConfig,
        TaskType,
        get_peft_model,
        AutoModelForCausalLM,
        AutoTokenizer,
        (Trainer, TrainingArguments, default_data_collator),
    )


class _TokenizedDataset:
    def __init__(self, records: list[dict[str, list[int]]]) -> None:
        self._records = records

    def __len__(self) -> int:
        return len(self._records)

    def __getitem__(self, idx: int) -> dict[str, list[int]]:
        return self._records[idx]


def load_jsonl_dataset(path: str | Path, *, max_samples: int | None = None) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                continue
            text = str(row.get("text") or "").strip()
            if not text:
                continue
            rows.append({"text": text})
            if max_samples is not None and len(rows) >= max_samples:
                break

    if not rows:
        raise ValueError(f"No usable training rows found in {path}")
    return rows


def _build_tokenized_dataset(rows: list[dict[str, str]], tokenizer: Any, max_seq_len: int) -> _TokenizedDataset:
    tokenized: list[dict[str, list[int]]] = []
    for row in rows:
        encoded = tokenizer(
            row["text"],
            truncation=True,
            max_length=max_seq_len,
            padding="max_length",
        )
        input_ids = list(encoded["input_ids"])
        attention_mask = list(encoded["attention_mask"])
        labels = [token if mask else -100 for token, mask in zip(input_ids, attention_mask)]
        tokenized.append(
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "labels": labels,
            }
        )

    return _TokenizedDataset(tokenized)


def train_and_export_adapter(config: FineTuneConfig) -> Path:
    (
        torch,
        LoraConfig,
        TaskType,
        get_peft_model,
        AutoModelForCausalLM,
        AutoTokenizer,
        trainer_bundle,
    ) = _lazy_import_ml_modules()
    Trainer, TrainingArguments, default_data_collator = trainer_bundle

    rows = load_jsonl_dataset(config.dataset_path, max_samples=config.max_samples)

    tokenizer = AutoTokenizer.from_pretrained(config.base_model_id, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    has_cuda = torch.cuda.is_available()
    dtype = torch.float16 if has_cuda else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        config.base_model_id,
        torch_dtype=dtype,
        device_map="auto" if has_cuda else None,
    )

    lora_cfg = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=config.lora_r,
        lora_alpha=config.lora_alpha,
        lora_dropout=config.lora_dropout,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "up_proj", "down_proj", "gate_proj"],
        inference_mode=False,
    )
    model = get_peft_model(model, lora_cfg)

    dataset = _build_tokenized_dataset(rows, tokenizer, config.max_seq_len)

    config.adapter_output_dir.mkdir(parents=True, exist_ok=True)
    work_dir = config.adapter_output_dir / "_trainer_tmp"
    work_dir.mkdir(parents=True, exist_ok=True)

    raw_args: dict[str, Any] = {
        "output_dir": str(work_dir),
        "overwrite_output_dir": True,
        "per_device_train_batch_size": config.batch_size,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "learning_rate": config.learning_rate,
        "num_train_epochs": config.num_train_epochs,
        "warmup_ratio": config.warmup_ratio,
        "logging_steps": config.logging_steps,
        "save_steps": config.save_steps,
        "save_total_limit": 1,
        "report_to": [],
        "fp16": has_cuda,
        "bf16": False,
        "remove_unused_columns": False,
    }

    supported = set(inspect.signature(TrainingArguments.__init__).parameters)
    filtered_args = {key: value for key, value in raw_args.items() if key in supported}
    args = TrainingArguments(**filtered_args)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset,
        data_collator=default_data_collator,
    )
    trainer.train()

    model.save_pretrained(config.adapter_output_dir, safe_serialization=True)
    tokenizer.save_pretrained(config.adapter_output_dir)

    validate_adapter_directory(config.adapter_output_dir)
    return config.adapter_output_dir
