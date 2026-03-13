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
4. Run benchmark replay on a sample trace: `scripts/run-benchmark.py examples/sample-trace.json --compare`.
5. Compile NDJSON telemetry into benchmark rows: `scripts/compile-trace.py traces/<session>.ndjson --rows-output benchmark.json --windows-output windows.json`.
6. Auto-label compiled rows with ontology constraints: `scripts/annotate-benchmark.py benchmark.json --output benchmark.annotated.json --print-ontology`.
7. Run the **full JIT inference loop** — send a live stream event and get a paging-aware decision: `POST /jit/route` on the running daemon. Returns the predicted adapter, paging status (`warm_hit`/`cold_miss`), current hot-set, and wall-clock prediction latency.

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

## Ground-truth labeling model

- LoRA-JIT uses an ontology-constrained labeling protocol.
- Labels include a primary adapter plus acceptable alternatives.
- Benchmark scoring is weighted for ambiguity-aware evaluation.
- Drop in `LlmLabelProvider` (set `LORA_JIT_LLM_API_BASE` + `LORA_JIT_LLM_API_KEY`) to upgrade from heuristic to LLM-powered annotation.

## Live telemetry defaults

- Enabled by default via `loraJit.telemetry.enabled`.
- Debounced flush tick: `loraJit.telemetry.tickMs = 75`.
- Max in-memory extension batch size before flush: `loraJit.telemetry.maxBatchSize = 200`.

This is intentionally an MVP skeleton; each subsystem exposes clear interfaces for iterative implementation.
