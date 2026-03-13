# Architecture (MVP)

## Components

- **Daemon (`backend/daemon`)**: API surface for health, telemetry routing, live telemetry ingestion, and benchmark execution.
- **Contracts (`backend/contracts`)**: Pydantic schemas used across daemon, tests, and extension payloads.
- **Routing (`backend/routing`)**: deterministic structural router + text and pseudo-embedding baselines.
- **Runtime (`backend/runtime`)**: interface for backend-specific adapter loading/activation.
- **Paging (`backend/paging`)**: adapter residency simulation for cache/miss accounting.
- **Benchmark (`backend/benchmark`)**: replay runner over recorded traces.
- **Telemetry Buffer (`backend/telemetry`)**: in-memory rolling buffer for streamed editor events.
- **VS Code Extension (`vscode-extension`)**: telemetry source and control-plane UX.

## API highlights

- `GET /health` — daemon health check.
- `POST /telemetry/route` — single routing decision from telemetry.
- `POST /telemetry/stream` — fire-and-forget batched event ingest for extension pipeline.
- `GET /telemetry/recent` — recent buffered events for trace validation/debugging.
- `POST /benchmark/run` — run one predictor against trace.
- `POST /benchmark/compare` — run structural/text/embedding and return winner.

## Live telemetry pipeline

- Extension records `document_open`, `document_save`, `cursor`, and `text_change` events.
- Text edits are sent as **deltas** (range + inserted text), not full-document snapshots.
- Events are buffered and flushed on a configurable tick (`loraJit.telemetry.tickMs`, default 75ms).
- Transport is intentionally **fire-and-forget** (extension does not await ingestion response).
- Daemon stores events in rolling memory for replay/trace capture workflows.

## Why this shape

The architecture isolates concerns so high-performance Linux runtime work can evolve without rewriting editor integration or benchmark methodology.
