from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def main() -> None:
    from backend.training.adapter_artifacts import REQUIRED_ADAPTER_FILES, validate_adapter_directory

    parser = argparse.ArgumentParser(description="Verify LoRA adapter artifact completeness")
    parser.add_argument("adapter_path", help="Path to adapters/<adapter_id>")
    args = parser.parse_args()

    path = validate_adapter_directory(Path(args.adapter_path))
    payload = {
        "adapter_path": str(path),
        "required_files": list(REQUIRED_ADAPTER_FILES),
        "status": "ok",
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
