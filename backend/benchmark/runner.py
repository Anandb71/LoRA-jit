from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Literal

from backend.contracts.schemas import BenchmarkComparisonResult, BenchmarkResult, TelemetryEvent
from backend.paging.simulator import PagingSimulator
from backend.routing.baselines import EmbeddingRouter, TextRouter
from backend.routing.structural import StructuralRouter


PredictorName = Literal["structural", "text", "embedding"]


class BenchmarkRunner:
    def __init__(self) -> None:
        self._fallback_adapter = "general"

    def _load_rows(self, trace_path: str) -> list[dict]:
        rows = json.loads(Path(trace_path).read_text(encoding="utf-8"))
        if not isinstance(rows, list):
            raise ValueError("Trace file must be a JSON array")
        return rows

    def _build_catalog(self, rows: list[dict]) -> list[str]:
        adapters: set[str] = set()
        for row in rows:
            expected = str(row.get("expected_adapter", self._fallback_adapter)).strip()
            if expected:
                adapters.add(expected)

            label = row.get("expected_label")
            if isinstance(label, dict):
                primary = str(label.get("primary_adapter", "")).strip()
                if primary:
                    adapters.add(primary)
                alternatives = label.get("acceptable_alternatives", [])
                if isinstance(alternatives, list):
                    adapters.update(str(item).strip() for item in alternatives if str(item).strip())

        if self._fallback_adapter not in adapters:
            adapters.add(self._fallback_adapter)
        return sorted(adapters)

    def _score_prediction(self, row: dict, predicted_adapter: str) -> float:
        label = row.get("expected_label")
        if isinstance(label, dict):
            primary = str(label.get("primary_adapter", self._fallback_adapter))
            alternatives = label.get("acceptable_alternatives", [])
            alternatives_set = {
                str(item)
                for item in alternatives
                if str(item)
            } if isinstance(alternatives, list) else set()

            if predicted_adapter == primary:
                return 1.0
            if predicted_adapter in alternatives_set:
                return 0.5
            return 0.0

        expected_adapter = str(row.get("expected_adapter", self._fallback_adapter))
        return 1.0 if predicted_adapter == expected_adapter else 0.0

    def _build_router(self, predictor: PredictorName, adapter_catalog: list[str]):
        if predictor == "structural":
            return StructuralRouter(fallback_adapter=self._fallback_adapter)
        if predictor == "text":
            return TextRouter(adapter_catalog=adapter_catalog, fallback_adapter=self._fallback_adapter)
        if predictor == "embedding":
            return EmbeddingRouter(adapter_catalog=adapter_catalog, fallback_adapter=self._fallback_adapter)
        raise ValueError(f"Unsupported predictor: {predictor}")

    def run_trace(self, trace_path: str, predictor: PredictorName = "structural") -> BenchmarkResult:
        rows = self._load_rows(trace_path)
        adapter_catalog = self._build_catalog(rows)
        router = self._build_router(predictor, adapter_catalog=adapter_catalog)
        paging = PagingSimulator(max_hot_adapters=3)

        total = 0
        score_sum = 0.0
        elapsed_ms_total = 0.0

        for row in rows:
            event = TelemetryEvent.model_validate(row["event"])
            started = time.perf_counter()
            decision = router.predict(event)
            elapsed_ms_total += (time.perf_counter() - started) * 1000

            paging.touch(decision.adapter_id)
            total += 1
            score_sum += self._score_prediction(row, predicted_adapter=decision.adapter_id)

        miss_rate = paging.stats.cold_misses / total if total else 0.0
        avg_ms = elapsed_ms_total / total if total else 0.0

        return BenchmarkResult(
            predictor=predictor,
            events_processed=total,
            top1_accuracy=(score_sum / total) if total else 0.0,
            cache_miss_rate=miss_rate,
            avg_prediction_ms=avg_ms,
        )

    def compare_predictors(
        self,
        trace_path: str,
        predictors: list[PredictorName] | None = None,
    ) -> BenchmarkComparisonResult:
        predictors = predictors or ["structural", "text", "embedding"]
        results = [self.run_trace(trace_path=trace_path, predictor=p) for p in predictors]
        winner = max(results, key=lambda r: (r.top1_accuracy, -r.cache_miss_rate)).predictor

        return BenchmarkComparisonResult(
            trace_path=trace_path,
            results=results,
            winner_by_accuracy=winner,
        )
