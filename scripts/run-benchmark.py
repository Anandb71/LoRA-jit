from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    from backend.benchmark.runner import BenchmarkRunner

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
