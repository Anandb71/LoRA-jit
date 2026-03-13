# LoRA-JIT

LoRA-JIT is a benchmark-first system for **structural adapter routing** on consumer hardware.

[![CI](https://github.com/Anandb71/LoRA-jit/actions/workflows/ci.yml/badge.svg)](https://github.com/Anandb71/LoRA-jit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

## What this repo currently includes

- Python backend scaffold for daemon, contracts, routing, runtime, paging, and benchmark replay.
- VS Code extension scaffold that can ping daemon health and send sample telemetry.
- Baseline docs for architecture and benchmark methodology.
- CI workflow covering Python tests/lint and extension type-check.

## Milestone 1 goal

Prove that structural routing can beat text/embedding baselines in adapter prediction quality and cache behavior using deterministic replay traces.

## Quick start (backend)

1. Create a Python 3.11+ environment.
2. Install dependencies from `pyproject.toml`.
3. Run the daemon entrypoint at `scripts/run-daemon.py`.

## Development standards

- License: [MIT](./LICENSE)
- Security policy: [SECURITY.md](./SECURITY.md)
- Contributing guide: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Code of conduct: [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)
- Changelog: [CHANGELOG.md](./CHANGELOG.md)

## Repository hygiene

- Automated CI for Python lint/tests and extension type-check.
- GitHub issue templates and pull request template.
- Editor and git normalization via `.editorconfig` and `.gitattributes`.

## Repo layout

- `backend/` — daemon, routing, runtime, paging, benchmark.
- `vscode-extension/` — VS Code integration client.
- `docs/` — architecture and benchmark specs.
- `tests/` — initial unit tests for contracts and simulator behavior.

This is intentionally an MVP skeleton; each subsystem exposes clear interfaces for iterative implementation.
