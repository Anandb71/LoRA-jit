# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Added
- `POST /jit/preload` endpoint for on-demand adapter warming.
- Approximate MB-budget paging in `PagingSimulator` via `LORA_JIT_MAX_HOT_MB` and
  `LORA_JIT_MAX_HOT_ADAPTERS`.
- `JitRoutingDecision` fields: `evicted_adapters`, `total_hot_mb`.
- Console entry points in package metadata:
  - `lora-jit-daemon`
  - `lora-jit-benchmark`
  - `lora-jit-compile`
  - `lora-jit-annotate`
- Minimal public Python API exports from `backend.__init__`.

### Changed
- Predictor protocol boundary now enforces `RoutingDecision` return type.
- Runtime config supports `LORA_JIT_STRICT_RUNTIME`.

### Fixed
- `PyTorchPeftRuntime.generate()` now handles tokenizer/model load failures inside strict fallback path.
- Runtime failures are now logged with structured metadata, and strict mode surfaces HTTP 500 from
  `/jit/complete` instead of silently returning stub text.

---

## [0.5.0] — 2026-03-16  `a43ed43`

### Added
- `POST /jit/complete` endpoint — generates tokens from the currently active runtime adapter.
- `CompletionRequest` and `CompletionResponse` Pydantic schemas.
- `generate(prompt, max_tokens) -> str` abstract method on `RuntimeBackend` interface.
- `MockRuntime.generate()` with 45 ms simulated latency and deterministic stub output.
- `PyTorchPeftRuntime.generate()` — real `model.generate()` under `torch.no_grad()` with
  tokenizer bootstrap, decode, and graceful fallback on error.
- `active_adapter_id` property on both runtime backends.
- VS Code extension: debounce-delayed `POST /jit/complete` calls after typing stops (280 ms).
- Extension logs completion text and generation latency to the `LoRA-JIT` output channel.
- Integration test: `test_daemon_jit_complete_endpoint` in `tests/test_jit_router.py`.
- Unit tests: `test_mock_runtime_generate_returns_completion`,
  `test_mock_runtime_tracks_active_adapter_id` in `tests/test_runtime_backend.py`.

---

## [0.4.0] — 2026-03-16  `ef778bf`

### Added
- Boot-time adapter preloading via `LORA_JIT_PRELOAD_ADAPTERS` env variable.
- `runtime_config_from_env()` now returns a `preload_adapters: list[str]` key.
- `create_runtime_backend()` iterates preload list and calls `preload_adapter()` for each.
- Daemon paging simulator is pre-warmed from the same list so first route events return
  `paging_status: warm_hit` instead of paying cold-miss latency.
- Unit tests: `test_runtime_config_parses_preload_adapters`,
  `test_factory_preloads_configured_adapters`.

### Changed
- Cold-start latency on first `/jit/route` drop from ~6 700 ms → ~6 ms when preload is set.

---

## [0.3.0] — 2026-03-15  `0d1184b`

### Added
- `scripts/build-sql-dataset.py` — generates 800-row curated SQL/Postgres SFT dataset.
- `scripts/train-peft-adapter.py` — fine-tunes `Qwen/Qwen1.5-0.5B` with LoRA and exports
  adapter weights to `adapters/<adapter_id>/`.
- `scripts/verify-adapter.py` — validates adapter artifact completeness.
- `PyTorchPeftRuntime` scaffold — opt-in real PEFT backend with lazy base model loading,
  `activate_adapter()` hot-swap, and graceful `MockRuntime` fallback.
- `create_runtime_backend()` factory respects `LORA_JIT_RUNTIME_BACKEND` env variable.
- PEFT-specific env variables: `LORA_JIT_BASE_MODEL_ID`, `LORA_JIT_ADAPTER_DIR`,
  `LORA_JIT_DEVICE`, `LORA_JIT_EAGER_LOAD`.
- Learned router: trainable multinomial Naive Bayes predictor backed by a JSON artifact.
- `scripts/train-router.py` — offline training from labeled benchmark rows.
- `examples/router-model.seed.json` and `examples/router-train.seed.json` — seed artifacts.
- `LORA_JIT_PREDICTOR=learned` and `LORA_JIT_ROUTER_MODEL_PATH` env variables.

---

## [0.2.0] — 2026-03-14  `fbbd07d`

### Added
- `POST /jit/route` endpoint — full JIT inference loop returning `JitRoutingDecision`.
- `JitRouter` orchestrator (predict → page → activate).
- `PagingSimulator` — LRU hot-set tracking with `warm_hit` / `cold_miss` semantics.
- `JitRoutingDecision` schema with paging status, hot-set snapshot, and latency fields.
- VS Code status bar item: `JIT: <adapter> (warm|cold)`.
- VS Code output channel with `[ROUTER]`, `[PAGING]`, `[INFER]`, `[TIMING]` log lines.
- `LlmLabelProvider` — optional LLM-backed offline labeling via OpenAI-compatible endpoint.
- Weighted multi-label benchmark scoring.
- `scripts/compile-trace.py` — state reconstruction and semantic window generation from NDJSON.
- `scripts/annotate-benchmark.py` — batch labeling with ontology validation.
- Runtime backend abstract interface (`RuntimeBackend`) with `activate_adapter()`.
- `MockRuntime` default backend.

---

## [0.1.0] — 2026-03-13  `7da7dce`

### Added
- Initial monorepo scaffold: `backend/`, `vscode-extension/`, `scripts/`, `tests/`, `docs/`.
- FastAPI daemon with `/health`, `/telemetry/route`, `/benchmark/run`, `/benchmark/compare`.
- Structural, text, and embedding routing baselines.
- Benchmark trace runner and predictor comparison harness.
- Ontology-constrained auto-labeler.
- Live telemetry streaming pipeline with debounced batch ingest.
- Sequence-aware trace repair via heartbeat resync.
- Trace persistence (append-only NDJSON per session).
- Rolling in-memory telemetry buffer with cap.
- CI workflow, MIT license, and OSS governance files.
