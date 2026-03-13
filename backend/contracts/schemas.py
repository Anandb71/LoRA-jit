from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    service: str = "lora-jit-daemon"
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TelemetryEvent(BaseModel):
    session_id: str
    file_path: str
    language_id: str
    cursor_line: int = Field(ge=0)
    cursor_column: int = Field(ge=0)
    symbols_in_scope: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RoutingDecision(BaseModel):
    session_id: str
    adapter_id: str
    confidence: float = Field(ge=0.0, le=1.0)
    candidates: list[str] = Field(default_factory=list)
    reason: str


class BenchmarkRequest(BaseModel):
    trace_path: str
    predictor: str = "structural"


class BenchmarkResult(BaseModel):
    predictor: str
    events_processed: int
    top1_accuracy: float
    cache_miss_rate: float
    avg_prediction_ms: float
