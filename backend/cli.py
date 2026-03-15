from __future__ import annotations

import argparse
import json
from pathlib import Path

import uvicorn

from backend.benchmark.trace_compiler import TraceCompiler
from backend.config.env import load_env_file
from backend.labeling.auto_labeler import annotate_compiled_rows
from backend.labeling.ontology import ontology_prompt_block


def _load_default_env() -> None:
    load_env_file(Path(__file__).resolve().parents[1] / ".env")


def daemon_main() -> None:
    """Run the LoRA-JIT daemon."""
    _load_default_env()
    from backend.daemon.app import app

    uvicorn.run(app, host="127.0.0.1", port=8765, reload=True)


def benchmark_main() -> None:
    """Run benchmark trace replay and optionally compare predictors."""
    from backend.benchmark.runner import BenchmarkRunner

    _load_default_env()
    parser = argparse.ArgumentParser(description="Run LoRA-JIT benchmark trace replay")
    parser.add_argument("trace", help="Path to JSON trace file")
    parser.add_argument(
        "--predictor",
        choices=["structural", "text", "embedding", "learned"],
        default="structural",
        help="Single predictor to run",
    )
    parser.add_argument("--compare", action="store_true", help="Run all predictors and output comparison")
    parser.add_argument("--output", default="", help="Optional output file path for JSON results")
    parser.add_argument("--model-path", default="", help="Optional learned-router model path")
    args = parser.parse_args()

    runner = BenchmarkRunner()
    if args.compare:
        predictors = ["structural", "text", "embedding", "learned"] if args.model_path else None
        result = runner.compare_predictors(
            trace_path=args.trace,
            predictors=predictors,
            model_path=args.model_path or None,
        )
        payload = result.model_dump(mode="json")
    else:
        result = runner.run_trace(
            trace_path=args.trace,
            predictor=args.predictor,
            model_path=args.model_path or None,
        )
        payload = result.model_dump(mode="json")

    text = json.dumps(payload, indent=2)
    print(text)

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote results to {output_path}")


def compile_trace_main() -> None:
    """Compile NDJSON telemetry trace into benchmark rows and windows."""
    _load_default_env()
    parser = argparse.ArgumentParser(description="Compile NDJSON telemetry trace into benchmark rows")
    parser.add_argument("trace", help="Path to session NDJSON trace")
    parser.add_argument("--rows-output", default="", help="Optional output path for benchmark rows JSON")
    parser.add_argument("--windows-output", default="", help="Optional output path for semantic windows JSON")
    args = parser.parse_args()

    compiler = TraceCompiler()
    trace_path = Path(args.trace)
    windows, rows = compiler.compile_session(trace_path)

    windows_payload = [
        {
            "session_id": w.session_id,
            "file_path": w.file_path,
            "symbol_path": w.symbol_path,
            "start_timestamp": w.start_timestamp.isoformat(),
            "end_timestamp": w.end_timestamp.isoformat(),
            "start_sequence_id": w.start_sequence_id,
            "end_sequence_id": w.end_sequence_id,
            "event_count": w.event_count,
            "document_text": w.document_text,
        }
        for w in windows
    ]

    rows_text = json.dumps(rows, indent=2)
    windows_text = json.dumps(windows_payload, indent=2)

    print(f"Compiled {len(windows)} windows and {len(rows)} benchmark rows")

    if args.rows_output:
        Path(args.rows_output).write_text(rows_text + "\n", encoding="utf-8")
        print(f"Wrote rows to {args.rows_output}")
    else:
        print(rows_text)

    if args.windows_output:
        Path(args.windows_output).write_text(windows_text + "\n", encoding="utf-8")
        print(f"Wrote windows to {args.windows_output}")


def annotate_main() -> None:
    """Annotate compiled benchmark rows with ontology-constrained labels."""
    _load_default_env()
    parser = argparse.ArgumentParser(description="Annotate compiled benchmark rows")
    parser.add_argument("input_rows", help="Path to compiled benchmark rows JSON")
    parser.add_argument("--output", required=True, help="Output path for annotated benchmark rows")
    parser.add_argument(
        "--print-ontology",
        action="store_true",
        help="Print adapter ontology block for external prompting",
    )
    args = parser.parse_args()

    rows = json.loads(Path(args.input_rows).read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("Input rows file must be a JSON array")

    annotated = annotate_compiled_rows(rows)
    out_text = json.dumps(annotated, indent=2)
    Path(args.output).write_text(out_text + "\n", encoding="utf-8")

    print(f"Annotated {len(annotated)} rows -> {args.output}")
    if args.print_ontology:
        print(ontology_prompt_block())
