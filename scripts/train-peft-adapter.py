from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.env import load_env_file  # noqa: E402

load_env_file(PROJECT_ROOT / ".env")


def main() -> None:
    from backend.training.peft_finetune import FineTuneConfig, train_and_export_adapter

    parser = argparse.ArgumentParser(
        description="Fine-tune and export a LoRA adapter directly into adapters/<adapter_id>/"
    )
    parser.add_argument("--adapter-id", default="sql_postgres", help="Adapter ID / output folder name")
    parser.add_argument(
        "--dataset",
        default="data/sql_postgres/train.jsonl",
        help="Path to JSONL SFT dataset with a `text` field",
    )
    parser.add_argument(
        "--adapter-dir",
        default=os.environ.get("LORA_JIT_ADAPTER_DIR", "adapters"),
        help="Root adapters directory",
    )
    parser.add_argument(
        "--base-model-id",
        default=os.environ.get("LORA_JIT_BASE_MODEL_ID", "Qwen/Qwen1.5-0.5B"),
        help="Base model ID",
    )
    parser.add_argument("--max-samples", type=int, default=800)
    parser.add_argument("--max-seq-len", type=int, default=512)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--lr", type=float, default=2e-4)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    args = parser.parse_args()

    output_dir = Path(args.adapter_dir) / args.adapter_id

    config = FineTuneConfig(
        base_model_id=args.base_model_id,
        dataset_path=Path(args.dataset),
        adapter_output_dir=output_dir,
        max_samples=args.max_samples,
        max_seq_len=args.max_seq_len,
        batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        lora_r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
    )

    out = train_and_export_adapter(config)

    payload = {
        "adapter_id": args.adapter_id,
        "base_model_id": args.base_model_id,
        "dataset": args.dataset,
        "output_dir": str(out),
        "files": sorted(path.name for path in out.iterdir()),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
