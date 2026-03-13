from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    from backend.benchmark.trace_compiler import TraceCompiler

    parser = argparse.ArgumentParser(description="Compile NDJSON telemetry trace into benchmark rows")
    parser.add_argument("trace", help="Path to session NDJSON trace")
    parser.add_argument(
        "--rows-output",
        default="",
        help="Optional output path for benchmark rows JSON",
    )
    parser.add_argument(
        "--windows-output",
        default="",
        help="Optional output path for semantic windows JSON",
    )
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


if __name__ == "__main__":
    main()
