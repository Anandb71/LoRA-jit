from __future__ import annotations

import json
from pathlib import Path

from backend.benchmark.runner import BenchmarkRunner
from backend.contracts.schemas import TelemetryEvent
from backend.routing.factory import create_predictor
from backend.routing.learned import LearnedRouter, LearnedRouterModel
from backend.training.router_trainer import LearnedRouterTrainer


def _training_rows() -> list[dict]:
    return [
        {
            "event": {
                "session_id": "s1",
                "file_path": "src/api/users.py",
                "language_id": "python",
                "cursor_line": 0,
                "cursor_column": 0,
                "symbols_in_scope": ["router", "create_user"],
                "metadata": {
                    "query": "fastapi router endpoint validation",
                    "code_block": "from fastapi import APIRouter\nrouter = APIRouter()",
                },
            },
            "expected_label": {
                "primary_adapter": "fastapi_service",
                "acceptable_alternatives": ["python_core"],
                "confidence": 0.95,
                "reasoning": "FastAPI endpoint code",
            },
            "expected_adapter": "fastapi_service",
        },
        {
            "event": {
                "session_id": "s2",
                "file_path": "db/query.sql",
                "language_id": "sql",
                "cursor_line": 0,
                "cursor_column": 0,
                "symbols_in_scope": ["user_query"],
                "metadata": {
                    "query": "postgres join query tuning",
                    "code_block": "SELECT * FROM users JOIN orders ON orders.user_id = users.id",
                },
            },
            "expected_label": {
                "primary_adapter": "sql_postgres",
                "acceptable_alternatives": ["data_engineering_general"],
                "confidence": 0.94,
                "reasoning": "SQL context",
            },
            "expected_adapter": "sql_postgres",
        },
    ]


def test_train_save_load_and_predict(tmp_path: Path) -> None:
    trainer = LearnedRouterTrainer()
    model = trainer.train(_training_rows(), augment_with_ontology=True)
    model_path = tmp_path / "router-model.json"
    model.save(model_path)

    router = LearnedRouter.load(model_path)
    event = TelemetryEvent(
        session_id="pred-1",
        file_path="backend/routes/user_api.py",
        language_id="python",
        cursor_line=1,
        cursor_column=1,
        symbols_in_scope=["router", "delete_user"],
        metadata={
            "query": "fastapi endpoint bug",
            "code_block": "from fastapi import APIRouter\nrouter = APIRouter()",
        },
    )

    decision = router.predict(event)
    assert decision.adapter_id == "fastapi_service"
    assert decision.reason == "learned multinomial_nb"
    assert decision.confidence >= 0.35


def test_factory_can_create_learned_router(tmp_path: Path) -> None:
    trainer = LearnedRouterTrainer()
    model = trainer.train(_training_rows(), augment_with_ontology=False)
    model_path = tmp_path / "router-model.json"
    model.save(model_path)

    predictor = create_predictor(predictor_name="learned", model_path=model_path)
    assert isinstance(predictor, LearnedRouter)


def test_benchmark_runner_supports_learned_predictor(tmp_path: Path) -> None:
    rows = _training_rows()
    trace_path = tmp_path / "rows.json"
    trace_path.write_text(json.dumps(rows), encoding="utf-8")

    trainer = LearnedRouterTrainer()
    model = trainer.train(rows, augment_with_ontology=True)
    model_path = tmp_path / "router-model.json"
    model.save(model_path)

    runner = BenchmarkRunner()
    result = runner.run_trace(
        trace_path=str(trace_path),
        predictor="learned",
        model_path=str(model_path),
    )

    assert result.predictor == "learned"
    assert result.events_processed == 2
    assert 0.0 <= result.top1_accuracy <= 1.0
    assert 0.0 <= result.cache_miss_rate <= 1.0


def test_model_round_trip_preserves_metadata(tmp_path: Path) -> None:
    model = LearnedRouterModel(
        adapters=["general", "python_core"],
        fallback_adapter="general",
        class_document_weights={"general": 1.0, "python_core": 2.0},
        class_token_totals={"general": 1.0, "python_core": 3.0},
        token_weights={"general": {"readme": 1.0}, "python_core": {"python": 2.0, "class": 1.0}},
        vocabulary=["class", "python", "readme"],
        trained_rows=3,
        metadata={"source_paths": ["seed.json"]},
    )
    model_path = tmp_path / "roundtrip.json"
    model.save(model_path)

    loaded = LearnedRouterModel.load(model_path)
    assert loaded.adapters == model.adapters
    assert loaded.metadata == model.metadata
