# LoRA-JIT Overview

## One sentence

LoRA-JIT is an **open, local-first orchestration layer** that watches your editor, routes intent to the right domain-specific LoRA adapter, pages adapters in and out of GPU memory, and generates completions — with **measurable** routing accuracy and latency at every step.

---

## The problem

General-purpose code models are mediocre at everything and excellent at nothing. Domain specialists (SQL, React, FastAPI, AWS SDK) are better — but only if you can **select the right one fast enough** to feel instant.

Today, most developers either:

- Use a **single cloud model** (Copilot, Cursor) with opaque routing and no local control
- Run **one local model** (Ollama, LM Studio) and accept weak cross-domain performance
- **Manually swap LoRA adapters** — slow, error-prone, not integrated with editor context

LoRA-JIT closes the gap: **automatic adapter routing from live editor signals**, with a benchmark harness to prove it works before you ship completions.

---

## What LoRA-JIT does

```
Editor telemetry → Intent classification → Adapter paging → GPU activation → Token generation
```

| Layer | Responsibility |
|-------|----------------|
| **VS Code extension** | Streams cursor, text, and symbol events; surfaces routing decisions in the status bar |
| **Control plane (FastAPI)** | Buffers telemetry, runs the router, manages paging state, records traces |
| **Runtime** | `MockRuntime` (default, CI-safe) or `PyTorchPeftRuntime` (real LoRA hot-swap) |
| **Benchmark harness** | Replay traces, compare predictors, train a lightweight learned router |

Every routing decision exposes: adapter ID, confidence, paging status (`warm_hit` / `cold_miss`), activation latency, and generation latency.

---

## What LoRA-JIT is not (yet)

Be honest when evaluating or adopting:

| Expectation | Reality today |
|-------------|---------------|
| Copilot-speed inline ghost text | Completions are **logged** to the output channel, not inserted inline |
| Works out of the box with trained adapters | Only `sql_postgres` has a full training recipe; other ontology adapters are registry entries |
| One-click VS Code Marketplace install | Extension runs via **Extension Development Host** (`F5`) |
| Real GPU VRAM paging | Paging is a **simulator** with LRU eviction; activation latency is real, VRAM telemetry is not |
| Sub-100 ms generation on laptop GPU | 40-token generation on RTX 3050 6 GB is ~7.5 s with Qwen1.5-0.5B |

LoRA-JIT is best understood as **routing infrastructure with observability**, not a finished consumer coding assistant.

---

## Who should use it

**Strong fit:**

- ML systems engineers building local LoRA/PEFT serving pipelines
- Privacy-conscious teams who cannot send code to the cloud
- Researchers who need reproducible routing benchmarks
- LoRA practitioners fine-tuning vertical domain models

**Weak fit (for now):**

- Developers expecting turnkey AI completions with no GPU setup
- Teams needing multi-user remote deployment (daemon binds `127.0.0.1` only)

---

## Design principles

1. **Benchmark-first** — routing quality is measured (`top1_accuracy`, `cache_miss_rate`), not assumed
2. **Separation of concerns** — telemetry, routing, paging, runtime, and benchmarks are isolated modules with shared Pydantic contracts
3. **Progressive complexity** — MockRuntime for CI and onboarding; PyTorch path for production GPU
4. **Ontology-constrained labels** — adapter IDs are registered; hallucinated labels fail validation
5. **Local-first** — no cloud dependency; optional LLM API only for offline benchmark annotation

---

## Measured results (reference hardware)

RTX 3050 6 GB laptop, `Qwen/Qwen1.5-0.5B` + `sql_postgres` LoRA:

| Metric | Value |
|--------|-------|
| Cold route (no preload) | ~6 700 ms |
| Warm route (preload enabled) | **~6 ms** |
| Subsequent warm routes | **6 – 20 ms** |
| 40-token generation | ~7 500 ms |
| Router confidence on SQL files | ~99 % |
| Test suite | **48 / 48 passing** |

See [BENCHMARK.md](./BENCHMARK.md) for methodology.

---

## Next steps

- **Try it in 10 minutes:** [QUICKSTART.md](./QUICKSTART.md)
- **Understand the architecture:** [ARCHITECTURE.md](./ARCHITECTURE.md)
- **Audit for production use:** [AUDIT.md](./AUDIT.md)
