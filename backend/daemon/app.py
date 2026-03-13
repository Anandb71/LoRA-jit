from __future__ import annotations

from fastapi import FastAPI

from backend.benchmark.runner import BenchmarkRunner
from backend.contracts.schemas import (
    BenchmarkComparisonRequest,
    BenchmarkComparisonResult,
    BenchmarkRequest,
    BenchmarkResult,
    HealthResponse,
    TelemetryBatchRequest,
    TelemetryBatchResponse,
    TelemetryEvent,
    TelemetryStreamEvent,
)
from backend.routing.structural import StructuralRouter
from backend.telemetry.buffer import TelemetryBuffer

app = FastAPI(title="LoRA-JIT Daemon", version="0.1.0")
router = StructuralRouter()
benchmark_runner = BenchmarkRunner()
telemetry_buffer = TelemetryBuffer(capacity=20_000)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/telemetry/route")
def route_from_telemetry(event: TelemetryEvent):
    return router.predict(event)


@app.post("/telemetry/stream", response_model=TelemetryBatchResponse)
def stream_telemetry(request: TelemetryBatchRequest) -> TelemetryBatchResponse:
    accepted = telemetry_buffer.append_many(request.events)
    return TelemetryBatchResponse(accepted=accepted, buffered_total=telemetry_buffer.size())


@app.get("/telemetry/recent", response_model=list[TelemetryStreamEvent])
def recent_telemetry(limit: int = 100) -> list[TelemetryStreamEvent]:
    return telemetry_buffer.recent(limit=limit)


@app.post("/benchmark/run", response_model=BenchmarkResult)
def run_benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    return benchmark_runner.run_trace(request.trace_path, predictor=request.predictor)


@app.post("/benchmark/compare", response_model=BenchmarkComparisonResult)
def compare_benchmarks(request: BenchmarkComparisonRequest) -> BenchmarkComparisonResult:
    return benchmark_runner.compare_predictors(
        trace_path=request.trace_path,
        predictors=request.predictors,
    )
