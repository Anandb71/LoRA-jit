# Benchmark Plan (MVP)

## Objective

Measure whether structural routing predicts the target adapter more accurately than fallback methods while reducing simulated cold misses.

## Current trace schema

Each trace row contains:
- `event`: telemetry payload compatible with `TelemetryEvent`
- `expected_adapter`: ground truth adapter label

## Reported metrics

- Top-1 accuracy
- Cache miss rate (from paging simulator)
- Average prediction latency (ms)

## MVP limitations

- Only `structural` predictor is implemented now.
- Text and embedding baselines will be added in next iteration.
