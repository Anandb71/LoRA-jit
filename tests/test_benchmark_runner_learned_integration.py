from __future__ import annotations

import json
from pathlib import Path

from backend.benchmark.runner import BenchmarkRunner
from backend.training.router_trainer import LearnedRouterTrainer


def test_compare_predictors_accepts_model_path_for_learned(tmp_path: Path) -> None:
    rows = [
        {
            "event": {
                "session_id": "s1",
                "file_path": "src/types/vector.ts",
                "language_id": "typescript",
                "cursor_line": 0,
                "cursor_column": 0,
                "symbols_in_scope": ["Vector"],
                "metadata": {
                    "query": "typescript interface bug",
                    "code_block": "export interface Vector<T> { x: T; y: T; }",
                },
            },
            "expected_label": {
                "primary_adapter": "typescript_core",
                "acceptable_alternatives": ["general"],
                "confidence": 0.9,
                "reasoning": "types",
            },
            "expected_adapter": "typescript_core",
        }
    ]
    trace_path = tmp_path / "rows.json"
    trace_path.write_text(json.dumps(rows), encoding="utf-8")

    trainer = LearnedRouterTrainer()
    model = trainer.train(rows, augment_with_ontology=True)
    model_path = tmp_path / "router-model.json"
    model.save(model_path)

    runner = BenchmarkRunner()
    comparison = runner.compare_predictors(
        trace_path=str(trace_path),
        predictors=["structural", "learned"],
        model_path=str(model_path),
    )
    assert {result.predictor for result in comparison.results} == {"structural", "learned"}
