# Benchmark Guide

## Purpose

The benchmark system answers a concrete measurable question:

> **Does the router choose the right adapter often enough, and does that choice reduce cold misses?**

LoRA-JIT treats routing as an engineering problem with numbers, not intuition.

---

## What gets measured

| Metric | Description |
|--------|-------------|
| `top1_accuracy` | Fraction of rows where the predicted adapter is correct (multi-label weighted) |
| `cache_miss_rate` | Fraction of route decisions that caused a cold miss in `PagingSimulator` |
| `avg_prediction_ms` | Mean wall-clock route time for the predictor under test |

---

## Available predictors

| Name | Strategy | Trainable |
|------|----------|-----------|
| `structural` | Heuristic token matching on file path, language ID, symbol path | No |
| `text` | Lexical overlap on path, language, symbols, `metadata.query`/`prompt` | No |
| `embedding` | Deterministic pseudo-embedding cosine similarity | No |
| `learned` | Multinomial Naive Bayes over tokenised event context | Yes |

All predictors share the same `predict(event) -> RoutingDecision` interface.

---

## Input row schema

Each benchmark row must contain:

```json
{
  "event": {
    "session_id": "...",
    "file_path": "...",
    "language_id": "...",
    "cursor_line": 0,
    "cursor_column": 0,
    "symbols_in_scope": [],
    "metadata": {}
  },
  "expected_adapter": "sql_postgres"
}
```

Or the richer multi-label form (produced by the auto-labeler):

```json
{
  "event": { ... },
  "expected_label": {
    "primary_adapter": "sql_postgres",
    "acceptable_alternatives": ["data_engineering_general"],
    "confidence": 0.92,
    "reasoning": "File contains parameterised PostgreSQL queries"
  }
}
```

---

## Quickstart

### Compare all predictors on the bundled sample

```powershell
python scripts/run-benchmark.py examples/sample-trace.json --compare
```

### Run a single predictor

```powershell
python scripts/run-benchmark.py examples/sample-trace.json --predictor structural
```

### Train and test the learned predictor

```powershell
# Train
python scripts/train-router.py examples/router-train.seed.json \
  --output examples/router-model.seed.json

# Benchmark
python scripts/run-benchmark.py examples/router-train.seed.json \
  --predictor learned \
  --model-path examples/router-model.seed.json
```

---

## Full trace-to-benchmark pipeline

### Step 1 — Compile a session trace

```powershell
python scripts/compile-trace.py traces/<session>.ndjson \
  --rows-output benchmark.rows.json \
  --windows-output benchmark.windows.json
```

What this does:

- Reconstructs file text from delta events and heartbeats
- Segments the session timeline into semantic windows
- Emits unlabeled benchmark rows with embedded code context snippets

### Step 2 — Auto-label the rows

```powershell
python scripts/annotate-benchmark.py benchmark.rows.json \
  --output benchmark.annotated.json \
  --print-ontology
```

What this does:

- Applies heuristic labeling rules based on file path, language, and symbols
- Validates all labels against `docs/ADAPTER_ONTOLOGY.md`
- Copies `primary_adapter` → `expected_adapter` for legacy predictor compatibility
- Optionally calls `LlmLabelProvider` for richer reasoning if `LORA_JIT_LLM_API_BASE` is set

### Step 3 — Benchmark

```powershell
python scripts/run-benchmark.py benchmark.annotated.json --compare
```

---

## Multi-label scoring

When `expected_label` is present:

| Prediction | Score |
|------------|-------|
| Matches `primary_adapter` | **1.0** |
| Matches an `acceptable_alternative` | **0.5** |
| Anything else | **0.0** |

`top1_accuracy` is the mean of per-row scores. This captures domain ambiguity honestly
rather than penalising valid alternative predictions as errors.

---

## Why ontology-constrained labeling matters

Without a fixed ontology, offline label generation can hallucinate adapter IDs that
do not exist in the runtime system. That silently corrupts benchmark comparisons.

LoRA-JIT prevents this by requiring all labels to use IDs from
[`docs/ADAPTER_ONTOLOGY.md`](./ADAPTER_ONTOLOGY.md).
The label parser rejects any ID outside the ontology before it can enter scoring.

This gives the benchmark two important properties:

1. Labels are **machine-checkable**
2. Comparisons across runs are **scientifically defensible**

---

## Interpreting results

The bundled `examples/sample-trace.json` is a **smoke test**, not a production benchmark.
All three baselines currently score `top1_accuracy = 1.0` on it because it is small and clean.

Meaningful benchmark results require:

- At least several hundred rows
- Coverage across multiple adapters and language IDs
- Real session traces from actual development activity

The benchmark infrastructure is production-ready; the bundled datasets are intentionally
minimal to keep the repository lightweight.
