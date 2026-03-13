# Benchmark Plan (MVP)

## Objective

Measure whether structural routing predicts the target adapter more accurately than fallback methods while reducing simulated cold misses.

## Current trace schema

Each trace row contains:
- `event`: telemetry payload compatible with `TelemetryEvent`
- `expected_adapter`: ground truth adapter label

Optional event metadata fields used by text/embedding baselines:
- `metadata.query`: natural-language intent text
- `metadata.prompt`: fallback prompt text

## Reported metrics

- Top-1 accuracy
- Cache miss rate (from paging simulator)
- Average prediction latency (ms)

## Predictors implemented

- `structural`: deterministic structural token heuristic.
- `text`: lexical overlap over query/prompt + context fields.
- `embedding`: deterministic pseudo-embedding cosine baseline.

## Running benchmark replay

- Single predictor: run `scripts/run-benchmark.py <trace> --predictor structural|text|embedding`
- Comparison run: `scripts/run-benchmark.py <trace> --compare`

## MVP limitations

- Embedding baseline is a deterministic proxy, not a model-embedding runtime yet.
- Paging is simulated rather than direct GPU residency management.
