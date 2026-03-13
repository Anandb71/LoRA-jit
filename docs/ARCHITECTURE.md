# Architecture (MVP)

## Components

- **Daemon (`backend/daemon`)**: API surface for health, telemetry routing, live telemetry ingestion, and benchmark execution.
- **Contracts (`backend/contracts`)**: Pydantic schemas used across daemon, tests, and extension payloads.
- **Routing (`backend/routing`)**: deterministic structural router + text and pseudo-embedding baselines + **JitRouter closed-loop orchestrator**.
- **Runtime (`backend/runtime`)**: interface for backend-specific adapter loading/activation.
- **Paging (`backend/paging`)**: adapter residency simulation for cache/miss accounting.
- **Benchmark (`backend/benchmark`)**: replay runner over recorded traces.
- **Trace Compiler (`backend/benchmark`)**: state reconstructor + semantic windowing from NDJSON logs.
- **Labeling (`backend/labeling`)**: adapter ontology + structured offline annotation pipeline + LLM-backed label provider.
- **Telemetry Buffer (`backend/telemetry`)**: in-memory rolling buffer for streamed editor events.
- **Sequence Tracker (`backend/telemetry`)**: per-session/per-file monotonic sequence continuity checks.
- **Trace Recorder (`backend/telemetry`)**: append-only NDJSON session logs for replay.
- **VS Code Extension (`vscode-extension`)**: telemetry source and control-plane UX.

## API highlights

- `GET /health` — daemon health check.
- `POST /telemetry/route` — legacy bare-prediction (no paging, kept for backward compat).
- `POST /jit/route` — **full JIT inference loop**: predict adapter → update paging → activate in runtime. Returns `JitRoutingDecision` with paging status and latency.
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
- **`LlmLabelProvider`** (`backend/labeling/llm_provider.py`) implements the `LabelProvider` protocol against any OpenAI-compatible endpoint. Configure via `LORA_JIT_LLM_API_BASE` and `LORA_JIT_LLM_API_KEY` env vars. Falls back to `HeuristicLabelProvider` on any error.

## JIT inference loop (Phase 3)

`JitRouter` (`backend/routing/jit_router.py`) closes the predict → page → activate loop:

```
TelemetryStreamEvent
  └─ JitRouter.route()
       ├─ bridge stream event → TelemetryEvent
       ├─ predictor.predict()  ← wall-clock timed
       ├─ PagingSimulator.touch()  ← warm_hit / cold_miss
       ├─ RuntimeBackend.activate_adapter()
       └─ JitRoutingDecision
            ├─ adapter_id, confidence, candidates, reason
            ├─ paging_status: "warm_hit" | "cold_miss"
            ├─ warm_adapters: list[str]  ← current hot-set snapshot
            └─ latency_prediction_ms
```

The daemon exposes this at `POST /jit/route`. The VS Code extension should switch from `/telemetry/route` to `/jit/route` to receive paging-aware decisions.

## Why this shape

The architecture isolates concerns so high-performance Linux runtime work can evolve without rewriting editor integration or benchmark methodology.
