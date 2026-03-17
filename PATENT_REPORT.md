# Patentability Assessment Report — LoRA-JIT

Date: 2026-03-16  
Project: `LoRA-jit`  
Prepared for: Internal research/patent planning

> **Important:** This is a technical patentability assessment, not legal advice. Final filing strategy and claim drafting should be reviewed by a registered patent attorney.

---

## 1) Executive summary

### Preliminary conclusion
**Potentially patentable, with moderate-to-strong prospects** if claims are focused on the **specific closed-loop orchestration** and **measurable latency-control mechanisms** rather than generic “adapter routing” alone.

### Why this is promising
The repository implements a concrete, testable system that combines:
- editor-context telemetry,
- adapter intent prediction,
- paging-aware warm/cold state transitions,
- runtime adapter activation,
- completion generation,
- strict failure semantics,
- measurable latency and cache telemetry.

This combination (especially with strict observability + preload + budget-aware eviction + editor loop integration) is stronger than a generic “use LoRA adapters dynamically” idea.

### Patentability confidence (technical, non-legal)
- **Novelty likelihood (technical):** 6.5 / 10
- **Non-obviousness likelihood (technical):** 7 / 10
- **Enablement/readiness:** 8.5 / 10
- **Overall filing-worthiness:** **High enough to pursue provisional filing promptly**

---

## 2) What appears invention-worthy

## A. Closed-loop editor-driven adapter orchestration
System flow implemented in code/docs:
1. Telemetry stream from IDE (`TelemetryStreamEvent`)
2. Route to adapter (`/jit/route`)
3. Paging decision (`warm_hit` / `cold_miss`)
4. Runtime activation (mock or real PEFT)
5. Completion generation (`/jit/complete`)
6. Feedback telemetry (latency, active adapter, evictions)

This is more than a standalone classifier; it is a measurable control loop.

## B. Latency-aware adapter residency management
Current architecture includes:
- count-capacity paging (`LORA_JIT_MAX_HOT_ADAPTERS`),
- optional MB-budget paging (`LORA_JIT_MAX_HOT_MB`),
- explicit eviction reporting (`evicted_adapters`, `total_hot_mb`),
- boot preload (`LORA_JIT_PRELOAD_ADAPTERS`) and runtime preload API (`POST /jit/preload`).

Potential claim angle: **preemptive and reactive residency control tied to predicted intent and measured activation latency**.

## C. Reliability mode for runtime safety
`LORA_JIT_STRICT_RUNTIME=true` changes behavior from fallback to explicit failure:
- runtime exceptions become observable,
- daemon surfaces HTTP 500 for generation failure,
- structured logging captures backend/adapter/error context.

Potential claim angle: **dual-mode inference reliability policy for dynamic adapter switching systems**.

## D. End-to-end measurable architecture
The project includes benchmark and replay pipelines that can demonstrate effect size:
- route latency,
- activation latency,
- warm/cold transition behavior,
- miss-rate impact.

This supports enablement and may strengthen non-obviousness arguments via empirical proof.

---

## 3) Main patent risks / attack vectors

1. **Prior art on MoE/tool-routing and adapter selection**
   - Generic “route request to specialist model” is likely crowded.
   - Mitigation: claim concrete loop mechanics, state transitions, and telemetry-driven residency management.

2. **Prior art on cache prefetch/eviction policies**
   - LRU and preloading by itself are not novel.
   - Mitigation: claim specific context-conditioned adapter-residency control in an IDE generation system with explicit activation-time feedback.

3. **Naming confusion around “JIT”**
   - If claims imply compiler/kernel JIT, examiner may find unrelated but strong JIT art.
   - Mitigation: define JIT as “just-in-time adapter activation,” not code compilation.

4. **Obviousness combinations**
   - Examiner may combine: (a) LoRA hot-swap references + (b) cache management + (c) editor telemetry.
   - Mitigation: emphasize concrete pipeline coupling, failure semantics, and measurable decision outputs used by UI and runtime behavior.

---

## 4) Candidate independent claim directions (technical draft)

## Claim Family 1 — Method claim
A computer-implemented method for adaptive inference in a code editor comprising:
- receiving editor telemetry events including file/path/language/symbol context,
- predicting an adapter identifier,
- updating adapter residency state using a hot-set policy,
- activating the predicted adapter in a runtime,
- generating completion text using the activated adapter,
- returning a response including at least one of paging status, activation latency, and runtime backend status.

## Claim Family 2 — Budget-aware residency control
A method where residency state is constrained by at least one of:
- adapter count budget and/or memory budget,
- with eviction of least-recently-used adapters,
- and where eviction metadata is returned in a route decision response.

## Claim Family 3 — Reliability mode for dynamic adapter runtimes
A method supporting dual runtime failure policies:
- permissive mode with fallback completion behavior,
- strict mode that raises generation failure and surfaces machine-readable error responses,
- where mode is runtime-configurable and tied to logging of adapter/runtime failure context.

## Claim Family 4 — Preload orchestration
A method enabling:
- startup preloading from configuration and/or on-demand preload requests,
- warming both runtime adapter state and paging state,
- reducing first-route activation latency in subsequent generation requests.

---

## 5) Evidence in this repository supporting enablement

Primary supporting artifacts:
- `backend/daemon/app.py` — `/jit/route`, `/jit/complete`, `/jit/preload` orchestration
- `backend/routing/jit_router.py` — predict → page → activate loop
- `backend/paging/simulator.py` — LRU touch, evictions, MB-budget handling
- `backend/runtime/pytorch_peft.py` — real adapter activation + generation + strict mode
- `backend/runtime/interface.py` — runtime abstraction and runtime error classes
- `backend/contracts/schemas.py` — response schemas carrying operational metrics
- `tests/test_jit_router.py` — integration coverage for route/complete/preload/error behavior
- `tests/test_runtime_backend.py` and `tests/test_paging_simulator.py` — strict mode and paging tests
- `docs/ARCHITECTURE.md`, `README.md` — architecture and measured behavior

This is strong for a provisional filing because implementation is concrete and reproducible.

---

## 6) What to add before filing (high impact)

1. **Ablation matrix (must-have)**
   - No preload vs preload
   - Count-only paging vs MB-budget paging
   - Strict mode off vs on
   - Learned predictor vs structural baseline

2. **Fixed benchmark protocol**
   - Freeze dataset(s), seeds, and hardware profile.
   - Export repeatable result tables per commit SHA.

3. **Prior-art aware terminology**
   - Use consistent term: “JIT adapter activation” throughout.

4. **Invention timeline package**
   - Commit hashes + dated experiment logs + architecture snapshots.

5. **Claim chart prep**
   - Build feature-to-code mapping table for each independent claim candidate.

---

## 7) Filing strategy (non-legal recommendation)

- **File provisional quickly** to establish priority while you continue improvements.
- Include broad system claim + narrower dependent claims around:
  - strict runtime behavior,
  - preload API behavior,
  - budget-aware eviction outputs,
  - telemetry-coupled route/activate/generate loop.
- Continue generating post-filing empirical data for non-provisional strengthening.

---

## 8) Bottom line

This project is not just a concept; it is an implemented, tested, measurable control-plane for dynamic LoRA adapter serving in an IDE context.

That makes it **plausibly patentable** if claims focus on the **specific integrated orchestration and runtime policy mechanisms**, not generic model routing.

If you want, next step can be a `docs/CLAIM_CHART_DRAFT.md` mapping each candidate claim element to exact code paths and tests.
