from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from fastapi import FastAPI
from fastapi import HTTPException

from backend.benchmark.runner import BenchmarkRunner
from backend.config.env import load_env_file
from backend.contracts.schemas import (
    BenchmarkComparisonRequest,
    BenchmarkComparisonResult,
    BenchmarkRequest,
    BenchmarkResult,
    CompletionRequest,
    CompletionResponse,
    HealthResponse,
    JitRoutingDecision,
    PreloadRequest,
    PreloadResponse,
    TelemetryBatchRequest,
    TelemetryBatchResponse,
    TelemetryEvent,
    TelemetryStreamEvent,
)
from backend.paging.simulator import PagingSimulator
from backend.routing.factory import create_predictor
from backend.routing.jit_router import JitRouter
from backend.runtime.factory import create_runtime_backend
from backend.runtime.pytorch_peft import runtime_config_from_env
from backend.telemetry.buffer import TelemetryBuffer
from backend.telemetry.sequence_tracker import SequenceTracker
from backend.telemetry.trace_recorder import TraceRecorder

logger = logging.getLogger(__name__)


def _estimate_adapter_sizes_mb(adapter_root: Path) -> dict[str, float]:
    sizes: dict[str, float] = {}
    if not adapter_root.exists():
        return sizes

    for sub in adapter_root.iterdir():
        if not sub.is_dir():
            continue
        total_bytes = 0
        for file_path in sub.rglob("*"):
            if file_path.is_file():
                total_bytes += file_path.stat().st_size
        sizes[sub.name] = max(total_bytes / (1024 * 1024), 1.0)
    return sizes


def _read_int_env(name: str, default: int) -> int:
    raw = os.environ.get(name, str(default)).strip()
    try:
        return int(raw)
    except ValueError:
        logger.warning("Invalid int for %s=%r; using default=%s", name, raw, default)
        return default


def _read_float_env(name: str) -> float | None:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        logger.warning("Invalid float for %s=%r; ignoring", name, raw)
        return None


load_env_file(Path(__file__).resolve().parents[2] / ".env")

app = FastAPI(title="LoRA-JIT Daemon", version="0.1.0")

# Legacy bare-prediction router (kept for backward compat)
router = create_predictor()

# Full JIT inference loop: predict → page → activate
_jit_backend = create_runtime_backend()
_runtime_cfg = runtime_config_from_env()
_paging_max_hot_adapters = _read_int_env("LORA_JIT_MAX_HOT_ADAPTERS", 3)
_paging_max_hot_mb = _read_float_env("LORA_JIT_MAX_HOT_MB")
_adapter_sizes_mb = _estimate_adapter_sizes_mb(Path(str(_runtime_cfg.get("adapter_dir", "adapters"))))
_jit_paging = PagingSimulator(
    max_hot_adapters=_paging_max_hot_adapters,
    max_hot_mb=_paging_max_hot_mb,
    adapter_sizes_mb=_adapter_sizes_mb,
)

for _adapter_id in list(_runtime_cfg.get("preload_adapters", [])):
    if str(_adapter_id).strip():
        _jit_paging.touch(str(_adapter_id).strip())
jit_router = JitRouter(backend=_jit_backend, paging=_jit_paging, predictor=create_predictor())

benchmark_runner = BenchmarkRunner()
telemetry_buffer = TelemetryBuffer(capacity=20_000)
sequence_tracker = SequenceTracker()
trace_recorder = TraceRecorder(root_dir=Path("traces"))


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.post("/telemetry/route")
def route_from_telemetry(event: TelemetryEvent):
    """Legacy bare-prediction endpoint (no paging, no runtime activation)."""
    return router.predict(event)


@app.post("/jit/route", response_model=JitRoutingDecision)
def jit_route(event: TelemetryStreamEvent) -> JitRoutingDecision:
    """Full JIT inference loop: predict adapter → update paging → activate in runtime.

    This is the production path. Returns an enriched decision that includes
    the paging status (warm_hit vs. cold_miss), the current hot-set, and
    the wall-clock prediction latency so the extension can surface VRAM
    pressure to the user.
    """
    return jit_router.route(event)


@app.post("/jit/complete", response_model=CompletionResponse)
def jit_complete(request: CompletionRequest) -> CompletionResponse:
    active_adapter = _jit_backend.active_adapter_id
    if not active_adapter:
        raise HTTPException(
            status_code=409,
            detail="No active adapter in runtime. Call /jit/route first to activate one.",
        )

    prompt = request.prefix
    if request.suffix:
        prompt = f"{request.prefix}\n\n# Right-context:\n{request.suffix}"

    started = time.perf_counter()
    try:
        completion = _jit_backend.generate(prompt=prompt, max_tokens=request.max_tokens)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "jit_complete_failed session_id=%s file_path=%s backend=%s adapter_id=%s strict=%s error_type=%s error=%s",
            request.session_id,
            request.file_path,
            _jit_backend.backend_name,
            active_adapter,
            bool(_runtime_cfg.get("strict_runtime", False)),
            type(exc).__name__,
            exc,
        )
        raise HTTPException(
            status_code=500,
            detail="Runtime generation failed. See daemon logs for details.",
        ) from exc

    generation_latency_ms = (time.perf_counter() - started) * 1000

    return CompletionResponse(
        completion_text=completion,
        active_adapter_used=active_adapter,
        generation_latency_ms=generation_latency_ms,
    )


@app.post("/jit/preload", response_model=PreloadResponse)
def jit_preload(request: PreloadRequest) -> PreloadResponse:
    preloaded: list[str] = []
    failed: dict[str, str] = {}

    for adapter_id in request.adapter_ids:
        candidate = str(adapter_id).strip()
        if not candidate:
            continue
        try:
            _jit_backend.preload_adapter(candidate)
            _jit_paging.touch(candidate)
            preloaded.append(candidate)
        except Exception as exc:  # noqa: BLE001
            failed[candidate] = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "jit_preload_failed adapter_id=%s backend=%s error_type=%s error=%s",
                candidate,
                _jit_backend.backend_name,
                type(exc).__name__,
                exc,
            )

    return PreloadResponse(
        requested=len(request.adapter_ids),
        preloaded=sorted(set(preloaded)),
        failed=failed,
    )


@app.post("/telemetry/stream", response_model=TelemetryBatchResponse)
def stream_telemetry(request: TelemetryBatchRequest) -> TelemetryBatchResponse:
    sequence_gaps = 0
    sessions_seen: set[str] = set()
    for event in request.events:
        sessions_seen.add(event.session_id)
        if sequence_tracker.observe(event):
            sequence_gaps += 1
        sequence_tracker.acknowledge_heartbeat(event)

    accepted = telemetry_buffer.append_many(request.events)
    trace_recorder.append_many(request.events)

    resync_files: set[str] = set()
    for session_id in sessions_seen:
        resync_files.update(sequence_tracker.pending_resync_files(session_id))

    return TelemetryBatchResponse(
        accepted=accepted,
        buffered_total=telemetry_buffer.size(),
        resync_files=sorted(resync_files),
        sequence_gaps_detected=sequence_gaps,
    )


@app.get("/telemetry/recent", response_model=list[TelemetryStreamEvent])
def recent_telemetry(limit: int = 100) -> list[TelemetryStreamEvent]:
    return telemetry_buffer.recent(limit=limit)


@app.get("/trace/sessions", response_model=list[str])
def list_trace_sessions() -> list[str]:
    return trace_recorder.list_sessions()


@app.get("/trace/session/{session_id}")
def get_trace_session_path(session_id: str):
    trace_path = trace_recorder.session_path(session_id)
    if not trace_path.exists():
        raise HTTPException(status_code=404, detail="Session trace not found")
    return {"session_id": session_id, "trace_path": str(trace_path.resolve())}


@app.post("/benchmark/run", response_model=BenchmarkResult)
def run_benchmark(request: BenchmarkRequest) -> BenchmarkResult:
    return benchmark_runner.run_trace(
        request.trace_path,
        predictor=request.predictor,
        model_path=request.model_path,
    )


@app.post("/benchmark/compare", response_model=BenchmarkComparisonResult)
def compare_benchmarks(request: BenchmarkComparisonRequest) -> BenchmarkComparisonResult:
    return benchmark_runner.compare_predictors(
        trace_path=request.trace_path,
        predictors=request.predictors,
        model_path=request.model_path,
    )
