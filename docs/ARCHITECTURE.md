# Architecture

## System overview

LoRA-JIT is organized as three cooperating layers:

1. **Editor telemetry layer** — the VS Code extension captures coding context and editor activity.
2. **Control-plane layer** — the daemon ingests telemetry, scores/benchmarks routes, and exposes the live JIT decision API.
3. **Execution layer** — the paging/runtime abstractions simulate adapter residency and activation today, while leaving room for a real runtime backend later.

The core design principle is separation of concerns: telemetry, routing, benchmark methodology, and runtime activation are isolated so each can evolve independently.

## Major components

- **Daemon (`backend/daemon`)** — FastAPI surface for health, telemetry ingest, live JIT route requests, and benchmark APIs.
- **Contracts (`backend/contracts`)** — Pydantic schemas shared across daemon, tests, and the extension.
- **Routing (`backend/routing`)** — baseline predictors, a trainable learned router, and `JitRouter`, the closed-loop orchestrator.
- **Runtime (`backend/runtime`)** — adapter activation abstraction; currently backed by `MockRuntime`.
- **Paging (`backend/paging`)** — hot-set simulation and cache statistics via `PagingSimulator`.
- **Benchmark (`backend/benchmark`)** — trace replay runner and comparison logic.
- **Trace Compiler (`backend/benchmark`)** — state reconstruction and semantic window generation from NDJSON logs.
- **Labeling (`backend/labeling`)** — ontology enforcement, heuristic labeling, and optional LLM-backed labeling.
- **Telemetry (`backend/telemetry`)** — rolling buffer, gap detection, and append-only trace persistence.
- **VS Code Extension (`vscode-extension`)** — telemetry producer and live JIT visualization surface.

## API surface

- `GET /health` — daemon health check.
- `POST /telemetry/route` — legacy single prediction endpoint without paging/runtime context.
- `POST /jit/route` — production JIT path; returns `JitRoutingDecision` with paging state and latency.
- `POST /jit/complete` — completion path; generates text from the currently active runtime adapter.
- `POST /telemetry/stream` — batched fire-and-forget telemetry ingest.
- `GET /telemetry/recent` — recent buffered telemetry for validation/debugging.
- `GET /trace/sessions` — list stored session trace IDs.
- `GET /trace/session/{session_id}` — resolve the trace file path for a session.
- `POST /benchmark/run` — benchmark a single predictor.
- `POST /benchmark/compare` — compare structural, text, and embedding baselines.

## Live request flows

### Telemetry ingest flow

1. VS Code records `document_open`, `document_save`, `text_change`, `cursor`, and `heartbeat` events.
2. Events are buffered locally and flushed on a short debounce interval.
3. The daemon ingests the batch, records it to an in-memory buffer and an NDJSON trace log, and checks sequence continuity.
4. If a gap is detected, the daemon requests a file resync via `resync_files` and the extension sends a full-text heartbeat.

### JIT route flow

1. The extension sends a `TelemetryStreamEvent` to `POST /jit/route`.
2. `JitRouter` bridges it into the leaner `TelemetryEvent` format used by predictors.
3. The active predictor selects an adapter. The daemon can load either a baseline or a trained learned model artifact via `.env`.
4. `PagingSimulator` updates the hot-set and marks the route as a `warm_hit` or `cold_miss`.
5. `RuntimeBackend.activate_adapter()` is invoked.
6. The daemon returns a `JitRoutingDecision` containing:
      - `adapter_id`
      - `confidence`
      - `candidates`
      - `reason`
      - `paging_status`
      - `warm_adapters`
      - `latency_prediction_ms`

### Completion flow

1. Extension sends `CompletionRequest` with `prefix` and optional `suffix`.
2. Daemon validates there is an active runtime adapter from the prior JIT route.
3. Runtime `generate(prompt, max_tokens)` produces completion text.
4. Daemon returns `CompletionResponse` with `completion_text`, `active_adapter_used`, and `generation_latency_ms`.

### Benchmark flow

1. Trace rows are replayed from JSON or compiled from NDJSON session traces.
2. Optional offline labeling adds `expected_label` with ontology-constrained alternatives.
3. Predictors are replayed over the same rows.
4. Accuracy, miss rate, and latency are compared.

## Telemetry design details

- Text edits are sent as **deltas**, not full-document snapshots.
- Every event includes a per-file monotonic `sequence_id`.
- Full-text heartbeats provide desync recovery.
- The extension enforces a hard local queue cap to avoid IDE memory blowouts.
- Cursor events include semantic scope via `symbol_path` when document symbols are available.

## Labeling architecture

The benchmark pipeline avoids “ground truth delusion” by forcing all labels through a fixed ontology.

- Valid adapter IDs are defined in [`docs/ADAPTER_ONTOLOGY.md`](./ADAPTER_ONTOLOGY.md).
- Labels use a structured schema with:
     - `primary_adapter`
     - `acceptable_alternatives`
     - `confidence`
     - `reasoning`
- The parser validates all model output against the ontology before the data can enter benchmark scoring.
- `LlmLabelProvider` supports any OpenAI-compatible endpoint via environment variables and falls back to the heuristic provider on failure.

## VS Code visualization path

The extension does more than silently ship telemetry now:

- A **status bar item** shows `JIT: <adapter> (warm|cold)`.
- A **dedicated output channel** logs router, cache, and inference events.
- The JIT route is debounced independently from telemetry streaming so the editor remains responsive.

This is important because it turns LoRA-JIT from an invisible backend into an observable systems demo.

## What is real vs simulated

### Real today

- Live editor telemetry capture
- Sequence-aware event repair
- Trace persistence and replay
- Ontology-constrained labeling
- Live JIT route responses and IDE visualization
- Offline training and live loading of a learned router artifact

### Simulated today

- Adapter residency and eviction policy
- Runtime activation side effects in the default `MockRuntime` path
- Production-grade routing quality beyond the shipped seed-trained model

That boundary is deliberate: the system is built so runtime realism can be upgraded without changing the telemetry or benchmark contracts.

## Runtime backend roadmap

The runtime abstraction now supports two tiers:

- **`MockRuntime`** — default backend for tests, CI, and lightweight local development
- **`PyTorchPeftRuntime`** — opt-in local backend that lazy-loads a base model and hot-swaps PEFT adapters from disk

`PyTorchPeftRuntime` now also supports an optional boot-time hot set through `.env`:

- `LORA_JIT_PRELOAD_ADAPTERS=adapter_a,adapter_b,...`

When set, the runtime preloads listed adapters during daemon startup so first route events can hit the warm activation path.

Important practical note: the repository does **not** ship real PEFT adapter folders under `adapters/`, so the PyTorch path remains opt-in and user-supplied.

The repository now includes scripts to close that gap locally:

- `scripts/build-sql-dataset.py` — generates a curated SQL/Postgres SFT dataset
- `scripts/train-peft-adapter.py` — fine-tunes and exports LoRA adapter weights into `adapters/<adapter_id>/`
- `scripts/verify-adapter.py` — validates adapter artifact completeness before runtime use

Why start with raw PyTorch/PEFT instead of vLLM?

- no separate inference server is required
- easier to run on a standard developer laptop
- direct access to adapter load/switch latency measurements
- preserves the runtime abstraction so a future `vLLMRuntime` can be added cleanly

This keeps LoRA-JIT honest: the LLM remains an offline teacher, while the hot path stays local and latency-sensitive.

## Why the architecture is shaped this way

LoRA-JIT is meant to answer two separate but related questions:

1. **Can we route adapter choice intelligently?**
2. **Can we keep the right adapter warm often enough for latency to matter?**

The architecture makes both questions measurable. That is the main value of the project.
