from __future__ import annotations

from pathlib import Path

from backend.routing.factory import create_predictor
from backend.routing.learned import LearnedRouter
from backend.routing.structural import StructuralRouter
from backend.training.router_trainer import LearnedRouterTrainer


def test_factory_falls_back_to_structural_when_model_missing(tmp_path: Path) -> None:
    predictor = create_predictor(
        predictor_name="learned",
        model_path=tmp_path / "missing-model.json",
    )
    assert isinstance(predictor, StructuralRouter)


def test_factory_uses_learned_model_when_present(tmp_path: Path) -> None:
    trainer = LearnedRouterTrainer()
    model = trainer.train(
        [
            {
                "event": {
                    "session_id": "seed",
                    "file_path": "backend/api/items.py",
                    "language_id": "python",
                    "cursor_line": 0,
                    "cursor_column": 0,
                    "symbols_in_scope": ["router", "list_items"],
                    "metadata": {
                        "query": "fastapi endpoint",
                        "code_block": "from fastapi import APIRouter",
                    },
                },
                "expected_label": {
                    "primary_adapter": "fastapi_service",
                    "acceptable_alternatives": ["python_core"],
                    "confidence": 0.9,
                    "reasoning": "seed",
                },
                "expected_adapter": "fastapi_service",
            }
        ],
        augment_with_ontology=True,
    )
    model_path = tmp_path / "router-model.json"
    model.save(model_path)

    predictor = create_predictor(predictor_name="learned", model_path=model_path)
    assert isinstance(predictor, LearnedRouter)
