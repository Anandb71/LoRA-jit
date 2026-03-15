from __future__ import annotations

import json
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from backend.contracts.schemas import RoutingDecision, TelemetryEvent

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
_DEFAULT_ALPHA = 1.0


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_RE.findall(text)]


def event_to_tokens(event: TelemetryEvent) -> list[str]:
    metadata = event.metadata or {}
    code_block = str(metadata.get("code_block") or "")[:4000]

    chunks = [
        event.file_path.replace("\\", "/"),
        event.language_id,
        " ".join(event.symbols_in_scope),
        str(metadata.get("query") or ""),
        str(metadata.get("prompt") or ""),
        str(metadata.get("semantic_context") or ""),
        code_block,
    ]

    tokens: list[str] = []
    for chunk in chunks:
        tokens.extend(_tokenize(chunk))

    language_token = event.language_id.strip().lower()
    if language_token:
        tokens.append(f"lang_{language_token}")

    suffix = Path(event.file_path).suffix.lstrip(".").lower()
    if suffix:
        tokens.append(f"ext_{suffix}")

    for symbol in event.symbols_in_scope:
        normalized = symbol.strip().lower()
        if normalized:
            tokens.append(f"sym_{normalized}")

    return [token for token in tokens if token]


@dataclass(slots=True)
class LearnedRouterModel:
    adapters: list[str]
    fallback_adapter: str
    class_document_weights: dict[str, float]
    class_token_totals: dict[str, float]
    token_weights: dict[str, dict[str, float]]
    vocabulary: list[str]
    alpha: float = _DEFAULT_ALPHA
    trained_rows: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "LearnedRouterModel":
        return cls(
            adapters=[str(item) for item in payload.get("adapters", [])],
            fallback_adapter=str(payload.get("fallback_adapter", "general")),
            class_document_weights={
                str(key): float(value)
                for key, value in dict(payload.get("class_document_weights", {})).items()
            },
            class_token_totals={
                str(key): float(value)
                for key, value in dict(payload.get("class_token_totals", {})).items()
            },
            token_weights={
                str(adapter): {str(token): float(weight) for token, weight in dict(weights).items()}
                for adapter, weights in dict(payload.get("token_weights", {})).items()
            },
            vocabulary=[str(item) for item in payload.get("vocabulary", [])],
            alpha=float(payload.get("alpha", _DEFAULT_ALPHA)),
            trained_rows=int(payload.get("trained_rows", 0)),
            metadata=dict(payload.get("metadata", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": 1,
            "model_type": "multinomial_nb",
            "adapters": list(self.adapters),
            "fallback_adapter": self.fallback_adapter,
            "class_document_weights": dict(self.class_document_weights),
            "class_token_totals": dict(self.class_token_totals),
            "token_weights": {adapter: dict(weights) for adapter, weights in self.token_weights.items()},
            "vocabulary": list(self.vocabulary),
            "alpha": self.alpha,
            "trained_rows": self.trained_rows,
            "metadata": dict(self.metadata),
        }

    def save(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.to_dict(), indent=2) + "\n", encoding="utf-8")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "LearnedRouterModel":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Learned router model must be a JSON object")
        return cls.from_dict(payload)


class LearnedRouter:
    """Lightweight trainable router using multinomial Naive Bayes over event tokens."""

    def __init__(self, model: LearnedRouterModel) -> None:
        self._model = model
        self._vocab_size = max(1, len(model.vocabulary))
        self._total_doc_weight = max(
            sum(model.class_document_weights.values()),
            float(len(model.adapters)) or 1.0,
        )

    @property
    def model(self) -> LearnedRouterModel:
        return self._model

    @classmethod
    def load(cls, path: str | Path) -> "LearnedRouter":
        return cls(LearnedRouterModel.load(path))

    def predict(self, event: TelemetryEvent) -> RoutingDecision:
        tokens = event_to_tokens(event)
        if not tokens:
            return RoutingDecision(
                session_id=event.session_id,
                adapter_id=self._model.fallback_adapter,
                confidence=0.35,
                candidates=[self._model.fallback_adapter],
                reason="learned fallback",
            )

        token_counts = Counter(tokens)
        scores: list[tuple[str, float]] = []

        for adapter in self._model.adapters:
            prior = math.log(
                (self._model.class_document_weights.get(adapter, 0.0) + self._model.alpha)
                / (self._total_doc_weight + (self._model.alpha * len(self._model.adapters)))
            )
            class_total = self._model.class_token_totals.get(adapter, 0.0)
            denom = class_total + (self._model.alpha * self._vocab_size)
            weights = self._model.token_weights.get(adapter, {})

            score = prior
            for token, count in token_counts.items():
                token_weight = weights.get(token, 0.0)
                score += count * math.log((token_weight + self._model.alpha) / denom)
            scores.append((adapter, score))

        scores.sort(key=lambda item: item[1], reverse=True)
        best_adapter, _ = scores[0]
        candidates = [adapter for adapter, _ in scores[:3]]
        confidence = self._confidence_from_scores(scores)

        return RoutingDecision(
            session_id=event.session_id,
            adapter_id=best_adapter,
            confidence=confidence,
            candidates=candidates,
            reason="learned multinomial_nb",
        )

    @staticmethod
    def _confidence_from_scores(scores: list[tuple[str, float]]) -> float:
        if not scores:
            return 0.35
        max_score = scores[0][1]
        exp_scores = [math.exp(score - max_score) for _, score in scores[:5]]
        total = sum(exp_scores) or 1.0
        return max(0.35, min(0.99, exp_scores[0] / total))
