# Benchmark Guide

## Goal

The benchmark system exists to answer a concrete question:

> **Does the router choose the right adapter often enough, and does that choice reduce cold misses?**

LoRA-JIT treats routing as a measurable systems problem, not a vibes problem.

## What gets measured

Each benchmark run reports:

- **Top-1 accuracy** — exact-match score, or weighted score when multi-label ground truth is present
- **Cache miss rate** — fraction of route decisions that caused a cold miss in `PagingSimulator`
- **Average prediction latency (ms)** — wall-clock route time for the predictor under test

## Predictors currently implemented

- `structural` — deterministic structural token heuristic
- `text` — lexical overlap over file path, language, symbols, and `metadata.query`/`metadata.prompt`
- `embedding` — deterministic pseudo-embedding cosine baseline

These are intentionally transparent baselines. The benchmark harness is designed to survive future predictor upgrades.

## Input row schema

Each benchmark row contains:

- `event` — payload compatible with `TelemetryEvent`
- `expected_adapter` — simple ground truth label, or
- `expected_label` — structured label with a primary adapter and acceptable alternatives

Optional metadata fields used by the text/embedding baselines:

- `metadata.query`
- `metadata.prompt`

## Fastest way to run the benchmark

### Compare all predictors on the sample trace

```powershell
python scripts/run-benchmark.py examples/sample-trace.json --compare
```

### Run only one predictor

```powershell
python scripts/run-benchmark.py examples/sample-trace.json --predictor structural
```

## Real workflow: trace → rows → labels → benchmark

### 1) Compile an NDJSON session trace

```powershell
python scripts/compile-trace.py traces/<session>.ndjson --rows-output benchmark.rows.json --windows-output benchmark.windows.json
```

What this does:

- reconstructs file text from deltas and heartbeats
- segments the timeline into semantic windows
- emits unlabeled benchmark rows with embedded code context

### 2) Annotate the compiled rows

```powershell
python scripts/annotate-benchmark.py benchmark.rows.json --output benchmark.annotated.json --print-ontology
```

What this does:

- adds `expected_label`
- validates the label against the adapter ontology
- copies `primary_adapter` into `expected_adapter` for compatibility

### 3) Benchmark the annotated rows

```powershell
python scripts/run-benchmark.py benchmark.annotated.json --compare
```

## Multi-label scoring

When `expected_label` is present, scoring is weighted:

- predict `primary_adapter` → **1.0**
- predict one of `acceptable_alternatives` → **0.5**
- predict anything else → **0.0**

This is what `top1_accuracy` currently reports for multi-label benchmark rows.

## Why the ontology matters

Without a fixed ontology, offline label generation can hallucinate adapters that do not exist in the runtime system.

LoRA-JIT prevents that by requiring all labels to use adapter IDs from [`docs/ADAPTER_ONTOLOGY.md`](./ADAPTER_ONTOLOGY.md).

That gives the benchmark two important properties:

- labels are **machine-checkable**
- comparisons remain **scientifically defensible**

## How to interpret current results

At the time of writing, `examples/sample-trace.json` is a smoke-test benchmark, not a realistic production benchmark.

Why?

- it contains only **2 rows**
- both are easy examples
- all three predictors score `1.0`

That result tells you the benchmark harness is working. It does **not** tell you the routing problem is solved.

## Current limitations

- The embedding baseline is a deterministic proxy, not a true embedding runtime.
- Paging is simulated rather than tied to actual GPU residency.
- The default auto-labeler is heuristic; `LlmLabelProvider` is intended for offline teacher-style labeling, not the hot path.
- The bundled example dataset is too small to support strong routing claims.

## What a serious next benchmark looks like

To make the benchmark genuinely persuasive, the next dataset should include:

- at least hundreds of windows, not two
- intentionally ambiguous cases
- cross-language tasks
- repeated adapter reuse patterns to stress paging behavior
- enough semantic diversity to separate structural from text/embedding approaches

When that exists, LoRA-JIT will be able to make stronger claims than “the demo works.” It will be able to make performance claims with evidence.
