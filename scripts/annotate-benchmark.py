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
    from backend.labeling.auto_labeler import annotate_compiled_rows
    from backend.labeling.ontology import ontology_prompt_block

    parser = argparse.ArgumentParser(description="Annotate compiled benchmark rows with ontology-constrained labels")
    parser.add_argument("input_rows", help="Path to compiled benchmark rows JSON")
    parser.add_argument("--output", required=True, help="Output path for annotated benchmark rows")
    parser.add_argument(
        "--print-ontology",
        action="store_true",
        help="Print adapter ontology block for external God-model prompting",
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


if __name__ == "__main__":
    main()
