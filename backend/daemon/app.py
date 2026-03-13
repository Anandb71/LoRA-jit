from __future__ import annotations

from fastapi import FastAPI

from backend.benchmark.runner import BenchmarkRunner
from backend.contracts.schemas import (
    BenchmarkComparisonRequest,
    BenchmarkComparisonResult,
    BenchmarkRequest,
    BenchmarkResult,
    HealthResponse,
    TelemetryEvent,
)
from backend.routing.structural import StructuralRouter

app = FastAPI(title="LoRA-JIT Daemon", version="0.1.0")
router = StructuralRouter()
benchmark_runner = BenchmarkRunner()


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/telemetry/route")
def route_from_telemetry(event: TelemetryEvent):
    return router.predict(event)


@app.post("/benchmark/run", response_model=BenchmarkResult)
def run_benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    return benchmark_runner.run_trace(request.trace_path, predictor=request.predictor)


@app.post("/benchmark/compare", response_model=BenchmarkComparisonResult)
def compare_benchmarks(request: BenchmarkComparisonRequest) -> BenchmarkComparisonResult:
    return benchmark_runner.compare_predictors(
        trace_path=request.trace_path,
        predictors=request.predictors,
    )
