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
    from backend.training.sql_dataset import generate_sql_postgres_examples, write_jsonl

    parser = argparse.ArgumentParser(description="Build a curated SQL/Postgres SFT dataset")
    parser.add_argument("--size", type=int, default=800, help="Number of training rows to generate")
    parser.add_argument("--seed", type=int, default=17, help="Random seed")
    parser.add_argument(
        "--output",
        default="data/sql_postgres/train.jsonl",
        help="Output JSONL file path",
    )
    args = parser.parse_args()

    rows = generate_sql_postgres_examples(size=args.size, seed=args.seed)
    out = write_jsonl(rows, args.output)
    print(json.dumps({"rows": len(rows), "output": str(out)}, indent=2))


if __name__ == "__main__":
    main()
