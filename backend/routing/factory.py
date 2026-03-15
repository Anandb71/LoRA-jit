from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Literal

from backend.labeling.ontology import list_adapter_ids
from backend.routing.baselines import EmbeddingRouter, TextRouter
from backend.routing.learned import LearnedRouter
from backend.routing.structural import StructuralRouter

PredictorName = Literal["structural", "text", "embedding", "learned"]
DEFAULT_ROUTER_MODEL_PATH = Path("examples/router-model.seed.json")

logger = logging.getLogger(__name__)


def routing_config_from_env() -> dict[str, str]:
    return {
        "predictor": os.environ.get("LORA_JIT_PREDICTOR", "structural").strip().lower(),
        "model_path": os.environ.get("LORA_JIT_ROUTER_MODEL_PATH", str(DEFAULT_ROUTER_MODEL_PATH)).strip(),
    }


def create_predictor(
    *,
    predictor_name: PredictorName | str | None = None,
    adapter_catalog: list[str] | None = None,
    fallback_adapter: str = "general",
    model_path: str | Path | None = None,
):
    config = routing_config_from_env()
    name = str(predictor_name or config["predictor"]).strip().lower()
    catalog = adapter_catalog or list_adapter_ids()

    if name == "structural":
        return StructuralRouter(fallback_adapter=fallback_adapter)
    if name == "text":
        return TextRouter(adapter_catalog=catalog, fallback_adapter=fallback_adapter)
    if name == "embedding":
        return EmbeddingRouter(adapter_catalog=catalog, fallback_adapter=fallback_adapter)
    if name == "learned":
        chosen_model_path = Path(model_path or config["model_path"])
        try:
            return LearnedRouter.load(chosen_model_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Falling back to StructuralRouter because learned model failed to load: %s: %s",
                type(exc).__name__,
                exc,
            )
            return StructuralRouter(fallback_adapter=fallback_adapter)

    logger.warning("Unknown predictor '%s'; falling back to structural", name)
    return StructuralRouter(fallback_adapter=fallback_adapter)
