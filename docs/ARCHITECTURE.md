# Architecture (MVP)

## Components

- **Daemon (`backend/daemon`)**: API surface for health, telemetry routing, and benchmark execution.
- **Contracts (`backend/contracts`)**: Pydantic schemas used across daemon, tests, and extension payloads.
- **Routing (`backend/routing`)**: deterministic structural router + text and pseudo-embedding baselines.
- **Runtime (`backend/runtime`)**: interface for backend-specific adapter loading/activation.
- **Paging (`backend/paging`)**: adapter residency simulation for cache/miss accounting.
- **Benchmark (`backend/benchmark`)**: replay runner over recorded traces.
- **VS Code Extension (`vscode-extension`)**: telemetry source and control-plane UX.

## API highlights

- `GET /health` — daemon health check.
- `POST /telemetry/route` — single routing decision from telemetry.
- `POST /benchmark/run` — run one predictor against trace.
- `POST /benchmark/compare` — run structural/text/embedding and return winner.

## Why this shape

The architecture isolates concerns so high-performance Linux runtime work can evolve without rewriting editor integration or benchmark methodology.
