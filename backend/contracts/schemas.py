from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str = "lora-jit-daemon"
    status: str = "ok"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TelemetryEvent(BaseModel):
    session_id: str
    file_path: str
    language_id: str
    cursor_line: int = Field(ge=0)
    cursor_column: int = Field(ge=0)
    symbols_in_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TextChangeDelta(BaseModel):
    range_start_line: int = Field(ge=0)
    range_start_character: int = Field(ge=0)
    range_end_line: int = Field(ge=0)
    range_end_character: int = Field(ge=0)
    text: str


class TelemetryStreamEvent(BaseModel):
    session_id: str
    event_type: Literal["cursor", "text_change", "document_open", "document_save", "heartbeat"]
    file_path: str
    language_id: str
    sequence_id: int = Field(ge=1)
    document_version: int | None = None
    cursor_line: int | None = Field(default=None, ge=0)
    cursor_column: int | None = Field(default=None, ge=0)
    full_text: str | None = None
    symbol_path: list[str] = Field(default_factory=list)
    deltas: list[TextChangeDelta] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class TelemetryBatchRequest(BaseModel):
    events: list[TelemetryStreamEvent] = Field(default_factory=list)


class TelemetryBatchResponse(BaseModel):
    accepted: int
    buffered_total: int
    resync_files: list[str] = Field(default_factory=list)
    sequence_gaps_detected: int = 0


class RoutingDecision(BaseModel):
    session_id: str
    adapter_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    candidates: list[str] = Field(default_factory=list)
    reason: str


class BenchmarkRequest(BaseModel):
    trace_path: str
    predictor: Literal["structural", "text", "embedding", "learned"] = "structural"
    model_path: str | None = None


class BenchmarkResult(BaseModel):
    predictor: Literal["structural", "text", "embedding", "learned"]
    events_processed: int
    top1_accuracy: float
    cache_miss_rate: float
    avg_prediction_ms: float


class BenchmarkComparisonRequest(BaseModel):
    trace_path: str
    predictors: list[Literal["structural", "text", "embedding", "learned"]] = Field(
        default_factory=lambda: ["structural", "text", "embedding"]
    )
    model_path: str | None = None


class BenchmarkComparisonResult(BaseModel):
    trace_path: str
    results: list[BenchmarkResult]
    winner_by_accuracy: str


class JitRoutingDecision(BaseModel):
    """Enriched routing decision from the JIT inference loop.

    Includes the base prediction plus paging-awareness and runtime activation status.
    """

    session_id: str
    adapter_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    candidates: list[str] = Field(default_factory=list)
    reason: str
    paging_status: Literal["warm_hit", "cold_miss"]
    warm_adapters: list[str] = Field(default_factory=list)
    latency_prediction_ms: float = Field(ge=0.0)
    activation_latency_ms: float = Field(default=0.0, ge=0.0)
    latency_total_ms: float = Field(default=0.0, ge=0.0)
    runtime_backend: str = "mock"
    sequence_id: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class CompletionRequest(BaseModel):
    session_id: str
    file_path: str
    prefix: str
    suffix: str = ""
    max_tokens: int = Field(default=64, ge=1, le=512)


class CompletionResponse(BaseModel):
    completion_text: str
    active_adapter_used: str
    generation_latency_ms: float = Field(ge=0.0)
