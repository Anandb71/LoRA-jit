from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.env import load_env_file  # noqa: E402

load_env_file(PROJECT_ROOT / ".env")


def main() -> None:
    from backend.routing.learned import LearnedRouter
    from backend.training.router_trainer import LearnedRouterTrainer

    parser = argparse.ArgumentParser(description="Train the LoRA-JIT learned router from labeled benchmark rows")
    parser.add_argument("inputs", nargs="+", help="One or more JSON benchmark row files")
    parser.add_argument("--output", required=True, help="Output path for the trained router JSON artifact")
    parser.add_argument(
        "--no-ontology-augmentation",
        action="store_true",
        help="Disable ontology seed examples during training",
    )
    args = parser.parse_args()

    trainer = LearnedRouterTrainer()
    rows = trainer.load_rows(args.inputs)
    model = trainer.train(
        rows,
        augment_with_ontology=not args.no_ontology_augmentation,
        source_paths=[str(Path(path)) for path in args.inputs],
    )
    output_path = model.save(args.output)

    metrics = trainer.evaluate_rows(rows, LearnedRouter(model))
    payload = {
        "output_path": str(output_path),
        "trained_rows": model.trained_rows,
        "adapters": model.adapters,
        "metrics": metrics,
        "metadata": model.metadata,
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
