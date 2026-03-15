from __future__ import annotations

import sys
from pathlib import Path

import uvicorn


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.env import load_env_file  # noqa: E402

load_env_file(PROJECT_ROOT / ".env")


if __name__ == "__main__":
    uvicorn.run("backend.daemon.app:app", host="127.0.0.1", port=8765, reload=True)
