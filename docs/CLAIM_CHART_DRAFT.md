# Claim Chart Draft — LoRA-JIT

Date: 2026-03-16  
Project: `LoRA-jit`  
Purpose: Attorney handoff document to reduce discovery time for provisional drafting.

> **Disclaimer:** Technical mapping only. Not legal advice and not final claim language.

---

## How to use this chart

- Column **"Claim Element"** = draft element for a potential independent/dependent claim.
- Column **"Implementation Mapping"** = exact code path, endpoint, class, or method implementing the element.
- Column **"Evidence"** = existing test/docs that corroborate enablement.
- Column **"Drafting notes"** = where to broaden or narrow language for filing.

---

## Family 1 — Core closed-loop method (editor telemetry → route → page → activate → generate)

| # | Claim Element (draft) | Implementation Mapping (exact) | Evidence (tests/docs) | Drafting notes |
|---|---|---|---|---|
| 1.1 | Receive editor-context telemetry event | `backend/contracts/schemas.py` → `TelemetryStreamEvent`; `backend/daemon/app.py` → `@app.post("/jit/route")` | `tests/test_jit_router.py::test_daemon_jit_route_endpoint`; `docs/ARCHITECTURE.md` telemetry section | Keep this broad to include IDEs beyond VS Code and multiple event types. |
| 1.2 | Convert stream telemetry to compact routing event representation | `backend/routing/jit_router.py` → `JitRouter._bridge()` maps stream fields to `TelemetryEvent` | `tests/test_jit_router.py::test_route_returns_jit_routing_decision` | Useful dependent claim: explicit transformation stage before predictor inference. |
| 1.3 | Predict adapter identifier from event context | `backend/routing/jit_router.py` → `decision = self._predictor.predict(te)`; predictor protocol in file | Predictor tests across suite + architecture docs | Claim as “model/domain adapter selection from coding context”. |
| 1.4 | Update residency state for predicted adapter | `backend/paging/simulator.py` → `PagingSimulator.touch(adapter_id)` | `tests/test_paging_simulator.py::test_paging_counts_hits_misses_and_evictions` | Include warm/cold state machine language. |
| 1.5 | Activate predicted adapter in runtime | `backend/routing/jit_router.py` → `self._backend.activate_adapter(...)`; runtime interface in `backend/runtime/interface.py` | `tests/test_runtime_backend.py::test_pytorch_peft_runtime_loads_adapter_once` | Claim should cover abstract runtime + concrete PEFT implementations. |
| 1.6 | Generate completion text with active adapter | `backend/daemon/app.py` → `/jit/complete`; runtime call `generate(prompt, max_tokens)` | `tests/test_jit_router.py::test_daemon_jit_complete_endpoint` | Include right-context/suffix conditioning as optional dependent feature. |
| 1.7 | Return enriched route/generation telemetry to caller | `backend/contracts/schemas.py` → `JitRoutingDecision`, `CompletionResponse`; `app.py` endpoint responses | Same tests + README/API docs | Strong element for practical utility; keep as response payload feature. |

---

## Family 2 — Budget-aware adapter residency control

| # | Claim Element (draft) | Implementation Mapping (exact) | Evidence (tests/docs) | Drafting notes |
|---|---|---|---|---|
| 2.1 | Maintain adapter hot-set with LRU behavior | `backend/paging/simulator.py` → `_hot` list reorder/evict logic in `touch()` | `tests/test_paging_simulator.py::test_paging_counts_hits_misses_and_evictions` | LRU alone likely prior art; combine with context-conditioned adapter switching. |
| 2.2 | Constrain residency by adapter count budget | `PagingSimulator.__init__(max_hot_adapters=...)`; daemon env parse `LORA_JIT_MAX_HOT_ADAPTERS` in `app.py` | Routing + paging tests | Dependent claim candidate. |
| 2.3 | Constrain residency by approximate memory budget | `PagingSimulator.__init__(max_hot_mb=...)`; `while ... _total_hot_mb() > max_hot_mb` | `tests/test_paging_simulator.py::test_paging_respects_mb_budget_and_evicts_lru` | This is a better novelty hook than plain count-LRU. |
| 2.4 | Track per-adapter memory estimate | `app.py` → `_estimate_adapter_sizes_mb()` and pass into `PagingSimulator(adapter_sizes_mb=...)` | Architecture + README | Claim can describe file-size-derived residency weighting. |
| 2.5 | Emit eviction metadata in route result | `schemas.py` → `evicted_adapters`, `total_hot_mb`; `jit_router.py` copies paging result into `JitRoutingDecision` | `tests/test_jit_router.py::test_daemon_jit_route_endpoint` asserts fields | Useful for claiming observability tied to orchestration decisions. |

---

## Family 3 — Preload orchestration (startup + on-demand)

| # | Claim Element (draft) | Implementation Mapping (exact) | Evidence (tests/docs) | Drafting notes |
|---|---|---|---|---|
| 3.1 | Startup preload from configuration | `backend/runtime/pytorch_peft.py` → `runtime_config_from_env()` parses `LORA_JIT_PRELOAD_ADAPTERS`; `backend/runtime/factory.py` preloads | `tests/test_runtime_backend.py::test_runtime_config_parses_preload_adapters`; `...::test_factory_preloads_configured_adapters` | Good dependent claim around proactive warm-set initialization. |
| 3.2 | Warm paging state from preloaded adapters | `backend/daemon/app.py` boot loop calls `_jit_paging.touch(...)` for preloaded IDs | README measured warm first-route behavior | Emphasize synchronization of runtime and paging layers. |
| 3.3 | On-demand preload API endpoint | `backend/daemon/app.py` → `@app.post("/jit/preload")` | `tests/test_jit_router.py::test_daemon_jit_preload_endpoint` | Strong practical claim element; distinguishes static config from runtime control. |
| 3.4 | Return preload success/failure map | `schemas.py` → `PreloadResponse(preloaded, failed)`; endpoint populates both lists/maps | Same test | Claim as machine-readable warm-up response contract. |

---

## Family 4 — Dual runtime reliability policy (strict vs permissive)

| # | Claim Element (draft) | Implementation Mapping (exact) | Evidence (tests/docs) | Drafting notes |
|---|---|---|---|---|
| 4.1 | Runtime policy flag controls failure behavior | `runtime_config_from_env()` reads `LORA_JIT_STRICT_RUNTIME`; injected into `PyTorchPeftRuntime(strict_runtime=...)` via `backend/runtime/factory.py` | `tests/test_runtime_backend.py::test_runtime_config_parses_preload_adapters` (strict flag parsing) | Broaden to “policy-configurable failure semantics”. |
| 4.2 | Permissive mode returns fallback completion on generation error | `backend/runtime/pytorch_peft.py` → `generate()` catches exception and returns fallback string when not strict | `tests/test_runtime_backend.py::test_pytorch_generate_returns_stub_when_not_strict` | Candidate dependent claim around non-throwing fallback path. |
| 4.3 | Strict mode raises explicit generation exception | `pytorch_peft.py` → raises `RuntimeGenerationError` when strict | `tests/test_runtime_backend.py::test_pytorch_generate_raises_when_strict` | Strong reliability/operational safety dependent claim. |
| 4.4 | Daemon surfaces strict runtime errors as API failure | `backend/daemon/app.py` `/jit/complete` catches runtime exception and raises HTTP 500 | `tests/test_jit_router.py::test_daemon_jit_complete_strict_runtime_raises_500` | Important for externally observable behavior and auditability. |
| 4.5 | Structured error logging includes backend/adapter/error context | `pytorch_peft.py` logger.exception fields in activation/generation; `app.py` logs session/file/backend/adapter/strict/error | Runtime and integration tests cover behavior paths | Claim language: “recording diagnostic metadata associated with runtime adapter operations.” |

---

## Family 5 — System claim (component architecture)

| Component | Concrete implementation |
|---|---|
| Telemetry ingestion module | `backend/daemon/app.py` (`/telemetry/stream`, schemas in `backend/contracts/schemas.py`) |
| Routing module | `backend/routing/jit_router.py` + predictor factory/baselines |
| Residency management module | `backend/paging/simulator.py` |
| Runtime activation/generation module | `backend/runtime/interface.py`, `backend/runtime/pytorch_peft.py`, `backend/runtime/mock_runtime.py` |
| Preload control module | `backend/runtime/factory.py` (startup preload), `backend/daemon/app.py` (`/jit/preload`) |
| Completion serving module | `backend/daemon/app.py` (`/jit/complete`) |
| Observability module | response schemas in `backend/contracts/schemas.py` + structured logging in daemon/runtime |

Drafting note: this table can become a system independent claim plus a non-transitory computer-readable medium claim set.

---

## Claim-language hardening notes for counsel

1. Prefer **"adapter activation and residency orchestration"** over generic "routing" wording.
2. Define JIT explicitly as **just-in-time adapter activation**, not compiler JIT.
3. Keep at least one independent claim that requires:
   - context-conditioned prediction,
   - residency update,
   - runtime activation,
   - generation,
   - response containing at least one operational metric.
4. Put likely-prior-art elements (LRU, preload alone) into dependent claims unless tightly integrated with telemetry-conditioned runtime decisions.

---

## Evidence package checklist (for provisional appendix)

- [x] API endpoint evidence: `/jit/route`, `/jit/complete`, `/jit/preload` in `backend/daemon/app.py`
- [x] Control loop implementation: `backend/routing/jit_router.py`
- [x] Residency logic: `backend/paging/simulator.py`
- [x] Strict/permissive runtime behavior: `backend/runtime/pytorch_peft.py`
- [x] Schema-level operational telemetry: `backend/contracts/schemas.py`
- [x] Integration tests for route/complete/preload/error paths: `tests/test_jit_router.py`
- [x] Unit tests for strict runtime and paging budget: `tests/test_runtime_backend.py`, `tests/test_paging_simulator.py`
- [ ] Add benchmark appendix tables with dated commit SHA and hardware profile
- [ ] Add ablation results (preload on/off, strict on/off, count-only vs MB-budget)

---

## Suggested immediate next artifacts

1. `docs/CLAIM_CHART_APPENDIX_EVIDENCE.md`
   - include run logs, command outputs, measured latency tables, and screenshots.
2. `docs/PROVISIONAL_APPENDIX_SPEC.md`
   - formalize definitions, embodiments, and alternative implementations.
3. `docs/ABLATION_RESULTS_YYYYMMDD.md`
   - reproducible matrix linked to commit SHA.

---

## Change log for this chart

- 2026-03-16: Initial draft created from current repository implementation and tests.
