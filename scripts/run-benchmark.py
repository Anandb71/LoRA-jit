from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.benchmark.runner import BenchmarkRunner


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LoRA-JIT benchmark trace replay")
    parser.add_argument("trace", help="Path to JSON trace file")
    parser.add_argument(
        "--predictor",
        choices=["structural", "text", "embedding"],
        default="structural",
        help="Single predictor to run",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Run all predictors and output comparison",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional output file path for JSON results",
    )
    args = parser.parse_args()

    runner = BenchmarkRunner()
    if args.compare:
        result = runner.compare_predictors(trace_path=args.trace)
        payload = result.model_dump(mode="json")
    else:
        result = runner.run_trace(trace_path=args.trace, predictor=args.predictor)
        payload = result.model_dump(mode="json")

    text = json.dumps(payload, indent=2)
    print(text)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote results to {output_path}")


if __name__ == "__main__":
    main()
