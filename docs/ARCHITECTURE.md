# Architecture

## Overview

LoRA-JIT is organised as four cooperating layers:

1. **Editor layer** — VS Code extension captures all IDE context and streams it to the daemon.
2. **Control-plane layer** — FastAPI daemon ingests telemetry, classifies intent, manages the adapter
   hot-set, and exposes the JIT decision API.
3. **Runtime layer** — adapter activation abstraction; `MockRuntime` for tests and CI,
   `PyTorchPeftRuntime` for real GPU inference.
4. **Benchmark layer** — offline trace replay, labeling pipeline, and predictor comparison harness.

The core design principle is **separation of concerns**: telemetry, routing, paging, runtime
activation, and benchmarking are isolated so each can evolve or be replaced independently.

---

## Component map

| Component | Path | Responsibility |
|-----------|------|----------------|
| Daemon | `backend/daemon/app.py` | FastAPI app — all HTTP endpoints |
| Contracts | `backend/contracts/schemas.py` | Pydantic schemas shared across all layers |
| JitRouter | `backend/routing/jit_router.py` | Closed-loop predict → page → activate orchestrator |
| Predictors | `backend/routing/` | `structural`, `text`, `embedding`, `learned` baselines |
| RuntimeBackend | `backend/runtime/interface.py` | Abstract `activate_adapter()` + `generate()` contract |
| MockRuntime | `backend/runtime/mock_runtime.py` | Deterministic stub for tests and CI |
| PyTorchPeftRuntime | `backend/runtime/pytorch_peft.py` | Real PEFT hot-swap on GPU |
| PagingSimulator | `backend/paging/simulator.py` | LRU hot-set tracking and cache statistics |
| BenchmarkRunner | `backend/benchmark/runner.py` | Trace replay and predictor scoring |
| TraceCompiler | `backend/benchmark/trace_compiler.py` | State reconstruction from NDJSON event logs |
| AutoLabeler | `backend/labeling/auto_labeler.py` | Ontology-constrained row labeling |
| LlmLabelProvider | `backend/labeling/llm_provider.py` | Optional LLM-backed offline labeling |
| TelemetryBuffer | `backend/telemetry/buffer.py` | Rolling in-memory event buffer |
| SequenceTracker | `backend/telemetry/sequence_tracker.py` | Per-file gap detection and resync |
| VS Code Extension | `vscode-extension/src/extension.ts` | Telemetry producer + JIT visualisation |

---

## HTTP API surface

| Method | Path | Schema in → out |
|--------|------|-----------------|
| `GET` | `/health` | → `HealthResponse` |
| `POST` | `/jit/route` | `TelemetryStreamEvent` → `JitRoutingDecision` |
| `POST` | `/jit/complete` | `CompletionRequest` → `CompletionResponse` |
| `POST` | `/telemetry/stream` | `TelemetryBatchRequest` → `TelemetryBatchResponse` |
| `GET` | `/telemetry/recent` | → `list[TelemetryStreamEvent]` |
| `GET` | `/trace/sessions` | → `list[str]` |
| `GET` | `/trace/session/{id}` | → `{path: str}` |
| `POST` | `/benchmark/run` | `BenchmarkRequest` → `BenchmarkResult` |
| `POST` | `/benchmark/compare` | `BenchmarkComparisonRequest` → `BenchmarkComparisonResult` |

---

## Data flows

### Telemetry ingest

```
VS Code extension
  -> debounced TelemetryBatchRequest
  -> POST /telemetry/stream
  -> TelemetryBuffer (rolling 20 000-event cap)
  -> NDJSON trace log (append-only, per session)
  -> SequenceTracker (gap detection)
  -> if gap: resync_files field in response triggers full-text heartbeat
```

### JIT route

```
VS Code extension (cursor / text_change event)
  -> POST /jit/route (TelemetryStreamEvent)
  -> JitRouter.route()
      -> predictor.predict()  [structural | text | embedding | learned]
      -> PagingSimulator.touch(adapter_id)          warm_hit or cold_miss
      -> RuntimeBackend.activate_adapter(adapter_id)
      -> return JitRoutingDecision
  -> extension updates status bar + output channel
```

### Completion

```
VS Code extension (280 ms debounce after typing stops)
  -> POST /jit/complete (CompletionRequest)
  -> daemon: check active_adapter_id is set
  -> RuntimeBackend.generate(prompt, max_tokens)
      MockRuntime:         45 ms sleep, returns stub text
      PyTorchPeftRuntime:  torch.no_grad() + tokenizer + model.generate()
  -> return CompletionResponse
  -> extension logs completion text + latency to output channel
```

### Benchmark

```
NDJSON trace
  -> TraceCompiler.compile()    reconstruct file state, emit benchmark rows
  -> AutoLabeler.annotate()     add expected_label via ontology-constrained rules
  -> BenchmarkRunner.run()      replay rows, score predictions
  -> BenchmarkResult            top1_accuracy, cache_miss_rate, avg_prediction_ms
```

---

## Paging simulator

`PagingSimulator` models adapter VRAM residency with a fixed-capacity LRU hot-set:

- `touch(adapter_id)` → `warm_hit` if already resident, `cold_miss` + LRU eviction if not
- `warm_adapters` snapshot returned with every routing decision
- capacity configurable (default: 3 simultaneous adapters)
- **Boot-time preloading** via `LORA_JIT_PRELOAD_ADAPTERS` — the daemon calls `touch()` for each
  listed adapter during startup so the first real route events hit the warm path

---

## Runtime backends

### MockRuntime (default)

- No ML dependencies required
- Tracks `_active_adapter` from `activate_adapter()` calls
- `generate()` sleeps 45 ms and returns a fixed stub string
- Used by all tests and CI; safe to run on any hardware

### PyTorchPeftRuntime (opt-in)

Activated by `LORA_JIT_RUNTIME_BACKEND=pytorch` in `.env`.

Boot sequence:

1. `runtime_config_from_env()` reads all `LORA_JIT_*` variables
2. `create_runtime_backend()` instantiates `PyTorchPeftRuntime`
3. If `LORA_JIT_EAGER_LOAD=true`, base model loaded immediately; otherwise lazy
4. If `LORA_JIT_PRELOAD_ADAPTERS` is set, those adapters are `preload_adapter()`-ed at boot
5. `activate_adapter(id)` hot-swaps the PEFT delta weights via `PeftModel.set_adapter()`
6. `generate(prompt, max_tokens)` runs `model.generate()` under `torch.no_grad()`

Graceful fallback: if any step in PyTorchPeftRuntime initialisation fails (missing model,
missing adapter, CUDA not available), `create_runtime_backend()` catches the exception, logs
a warning, and silently returns `MockRuntime`.

### Adapter directory layout

```
adapters/
  sql_postgres/
    adapter_config.json       PEFT adapter config (r, lora_alpha, target_modules …)
    adapter_model.safetensors LoRA delta weights
    tokenizer.json            tokenizer vocab
    tokenizer_config.json     tokenizer settings
    chat_template.jinja       optional chat template
```

---

## Telemetry design

- All edits sent as **delta events** (range + text), never full-document snapshots
- Every event carries a per-file monotonic `sequence_id`
- Full-text **heartbeat** events provide desync recovery
- Extension enforces a hard local queue cap to prevent IDE memory pressure
- Cursor events include semantic scope via `symbol_path` when document symbols are available
- Trace files are append-only NDJSON, one file per session, stored under `traces/`

---

## Labeling and ontology

All benchmark labels are validated against the fixed adapter ontology in
`docs/ADAPTER_ONTOLOGY.md`. This prevents hallucinated adapter IDs from corrupting benchmarks.

Label schema:

```json
{
  "primary_adapter": "sql_postgres",
  "acceptable_alternatives": ["data_engineering_general"],
  "confidence": 0.92,
  "reasoning": "File contains PostgreSQL DDL and parameterised queries"
}
```

Scoring:

- Predict `primary_adapter` → **1.0**
- Predict an `acceptable_alternative` → **0.5**
- Predict anything else → **0.0**

`LlmLabelProvider` calls any OpenAI-compatible endpoint for richer reasoning.
Fallback to heuristic labeling on network error (configurable).

---

## VS Code extension architecture

```
onDidChangeCursorPosition  -> debounce 150 ms -> POST /jit/route
onDidChangeTextDocument    -> debounce 280 ms -> POST /jit/complete
                                              -> POST /telemetry/stream
```

On each `/jit/route` response:
- Status bar updated: `JIT: <adapter_id> (warm|cold)`
- Output channel: `[ROUTER]`, `[PAGING]`, `[INFER]`, `[TIMING]` lines

On each `/jit/complete` response:
- Output channel: completion text preview + generation latency

Errors are logged to the output channel and never surface as modal popups.
409 from `/jit/complete` (no active adapter yet) is silently ignored.

---

## Predictor comparison

| Predictor | Strategy | Trainable |
|-----------|----------|-----------|
| `structural` | Heuristic token matching on file path, language ID, symbol path | No |
| `text` | Lexical overlap on file path, language, symbols, query/prompt metadata | No |
| `embedding` | Deterministic pseudo-embedding cosine similarity | No |
| `learned` | Multinomial Naive Bayes over tokenised event context | Yes — JSON artifact |

All predictors implement the same `predict(event: TelemetryEvent) -> RoutingDecision` interface
so they are interchangeable in both the benchmark runner and the live daemon.

---

## What is real vs simulated

### Real today

- Live editor telemetry capture and sequence-aware repair
- Trace persistence and offline replay
- Ontology-constrained benchmark labeling
- Full JIT route and completion API with measured latency
- Offline training and live loading of the learned router
- Real PEFT adapter training, export, and hot-swap (`PyTorchPeftRuntime`)
- Boot-time adapter preloading with warm first-route latency

### Simulated / mocked in default config

- Adapter VRAM residency is tracked by `PagingSimulator`, not measured from actual GPU memory
- `MockRuntime` is the default backend; `PyTorchPeftRuntime` is opt-in

The boundary is deliberate: the systems design is fully testable without ML dependencies,
and the ML path can be switched on without changing any contracts.

---

## Why this architecture

LoRA-JIT is designed to answer two measurable questions:

1. **Can we route adapter choice intelligently from editor context?**
2. **Can we keep the right adapter warm often enough for latency to matter?**

The architecture makes both questions independently measurable and improvable.
