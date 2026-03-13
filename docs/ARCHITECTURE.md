# Architecture (MVP)

## Components

- **Daemon (`backend/daemon`)**: API surface for health, telemetry routing, and benchmark execution.
- **Contracts (`backend/contracts`)**: Pydantic schemas used across daemon, tests, and extension payloads.
- **Routing (`backend/routing`)**: deterministic structural heuristic router (replaceable).
- **Runtime (`backend/runtime`)**: interface for backend-specific adapter loading/activation.
- **Paging (`backend/paging`)**: adapter residency simulation for cache/miss accounting.
- **Benchmark (`backend/benchmark`)**: replay runner over recorded traces.
- **VS Code Extension (`vscode-extension`)**: telemetry source and control-plane UX.

## Why this shape

The architecture isolates concerns so high-performance Linux runtime work can evolve without rewriting editor integration or benchmark methodology.
