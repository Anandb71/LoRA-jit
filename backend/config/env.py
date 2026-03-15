from __future__ import annotations

import os
from pathlib import Path


def load_env_file(path: str | Path = ".env", *, override: bool = False) -> bool:
    """Load a simple .env file into ``os.environ`` if present.

    This keeps the project dependency-light while making the checked-in
    ``.env`` file actually influence local scripts and daemon startup.
    """
    env_path = Path(path)
    if not env_path.exists():
        return False

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = value

    return True
