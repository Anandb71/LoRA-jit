# Architecture (MVP)

## Components

- **Daemon (`backend/daemon`)**: API surface for health, telemetry routing, live telemetry ingestion, and benchmark execution.
- **Contracts (`backend/contracts`)**: Pydantic schemas used across daemon, tests, and extension payloads.
- **Routing (`backend/routing`)**: deterministic structural router + text and pseudo-embedding baselines.
- **Runtime (`backend/runtime`)**: interface for backend-specific adapter loading/activation.
- **Paging (`backend/paging`)**: adapter residency simulation for cache/miss accounting.
- **Benchmark (`backend/benchmark`)**: replay runner over recorded traces.
- **Trace Compiler (`backend/benchmark`)**: state reconstructor + semantic windowing from NDJSON logs.
- **Labeling (`backend/labeling`)**: adapter ontology + structured offline annotation pipeline.
- **Telemetry Buffer (`backend/telemetry`)**: in-memory rolling buffer for streamed editor events.
- **Sequence Tracker (`backend/telemetry`)**: per-session/per-file monotonic sequence continuity checks.
- **Trace Recorder (`backend/telemetry`)**: append-only NDJSON session logs for replay.
- **VS Code Extension (`vscode-extension`)**: telemetry source and control-plane UX.

## API highlights

- `GET /health` — daemon health check.
- `POST /telemetry/route` — single routing decision from telemetry.
- `POST /telemetry/stream` — fire-and-forget batched event ingest for extension pipeline.
- `GET /telemetry/recent` — recent buffered events for trace validation/debugging.
- `GET /trace/sessions` — list captured trace sessions.
- `GET /trace/session/{session_id}` — resolve on-disk NDJSON path for a trace session.
- `POST /benchmark/run` — run one predictor against trace.
- `POST /benchmark/compare` — run structural/text/embedding and return winner.

## Live telemetry pipeline

- Extension records `document_open`, `document_save`, `cursor`, and `text_change` events.
- Text edits are sent as **deltas** (range + inserted text), not full-document snapshots.
- Every event carries a per-file monotonic `sequence_id`.
- Events are buffered and flushed on a configurable tick (`loraJit.telemetry.tickMs`, default 75ms).
- Extension enforces a hard queue ceiling (`loraJit.telemetry.hardBufferLimit`, default 1000) and drops queued events to protect IDE memory.
- Extension emits full-text `heartbeat` events periodically and on document open/save.
- Transport is intentionally **fire-and-forget** (extension does not await ingestion response).
- Daemon detects sequence gaps and returns `resync_files` hints for heartbeat repair.
- Cursor events include semantic context (`symbol_path`) from document symbols when available.
- Daemon stores events in rolling memory for replay/trace capture workflows.

## Trace compiler flow (Phase 1)

1. Reconstruct per-file text state by replaying ordered deltas and heartbeat full-text snapshots.
2. Segment timeline into semantic windows whenever file/symbol context changes.
3. Emit benchmark rows with `label_status = pending_offline_annotation` and embedded code block context.
4. (Next phase) offline auto-labeler assigns high-quality `expected_adapter` ground truth.

## Auto-labeler architecture (Phase 2)

- Ontology defines the only valid adapter IDs.
- Label provider must emit structured output with:
	- `primary_adapter`
	- `acceptable_alternatives`
	- `confidence`
	- `reasoning`
- Parser validates output against ontology before benchmark ingestion.
- Benchmark runner applies weighted scoring (1.0 primary, 0.5 acceptable alternative).

## Why this shape

The architecture isolates concerns so high-performance Linux runtime work can evolve without rewriting editor integration or benchmark methodology.
