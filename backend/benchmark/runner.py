from __future__ import annotations

import json
import time
from pathlib import Path

from backend.contracts.schemas import BenchmarkResult, TelemetryEvent
from backend.paging.simulator import PagingSimulator
from backend.routing.structural import StructuralRouter


class BenchmarkRunner:
    def __init__(self) -> None:
        self.router = StructuralRouter()
        self.paging = PagingSimulator(max_hot_adapters=3)

    def run_trace(self, trace_path: str, predictor: str = "structural") -> BenchmarkResult:
        if predictor != "structural":
            raise ValueError("Only 'structural' predictor is implemented in MVP skeleton")

        rows = json.loads(Path(trace_path).read_text(encoding="utf-8"))
        total = 0
        correct = 0
        elapsed_ms_total = 0.0

        for row in rows:
            event = TelemetryEvent.model_validate(row["event"])
            expected_adapter = row.get("expected_adapter", "general")

            started = time.perf_counter()
            decision = self.router.predict(event)
            elapsed_ms_total += (time.perf_counter() - started) * 1000

            self.paging.touch(decision.adapter_id)
            total += 1
            if decision.adapter_id == expected_adapter:
                correct += 1

        miss_rate = self.paging.stats.cold_misses / total if total else 0.0
        avg_ms = elapsed_ms_total / total if total else 0.0

        return BenchmarkResult(
            predictor=predictor,
            events_processed=total,
            top1_accuracy=(correct / total) if total else 0.0,
            cache_miss_rate=miss_rate,
            avg_prediction_ms=avg_ms,
        )
