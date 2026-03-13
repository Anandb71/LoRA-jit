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

## Trace-to-benchmark compile (Phase 1)

- Compile append-only NDJSON session traces into semantic windows + benchmark rows:
	- `scripts/compile-trace.py <trace.ndjson> --rows-output <rows.json> --windows-output <windows.json>`
- Phase 1 output rows are intentionally unlabeled (`label_status = pending_offline_annotation`).
- Next phase (offline auto-labeler) should assign `expected_adapter` using a heavy model over `metadata.code_block`.

## MVP limitations

- Embedding baseline is a deterministic proxy, not a model-embedding runtime yet.
- Paging is simulated rather than direct GPU residency management.
- Compiler currently emits unlabeled fixtures; offline ground-truth annotation is the next stage.
