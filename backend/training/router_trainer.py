from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from backend.contracts.schemas import TelemetryEvent
from backend.labeling.ontology import ADAPTER_ONTOLOGY, ensure_known_adapter
from backend.routing.learned import LearnedRouter, LearnedRouterModel, event_to_tokens


class LearnedRouterTrainer:
    def __init__(self, fallback_adapter: str = "general") -> None:
        self._fallback_adapter = fallback_adapter

    def load_rows(self, paths: list[str | Path]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in paths:
            payload = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise ValueError(f"Training data file must be a JSON array: {path}")
            rows.extend(payload)
        return rows

    def train(
        self,
        rows: list[dict[str, Any]],
        *,
        augment_with_ontology: bool = True,
        source_paths: list[str] | None = None,
    ) -> LearnedRouterModel:
        class_document_weights: defaultdict[str, float] = defaultdict(float)
        class_token_weights: defaultdict[str, Counter[str]] = defaultdict(Counter)
        vocabulary: set[str] = set()

        row_count = 0
        for row in rows:
            event = TelemetryEvent.model_validate(row["event"])
            tokens = event_to_tokens(event)
            if not tokens:
                tokens = [self._fallback_adapter]

            for adapter_id, weight in self._label_weights(row).items():
                class_document_weights[adapter_id] += weight
                class_token_weights[adapter_id].update({token: weight for token in tokens})
                vocabulary.update(tokens)
            row_count += 1

        if augment_with_ontology:
            for entry in ADAPTER_ONTOLOGY:
                tokens = event_to_tokens(
                    TelemetryEvent(
                        session_id="ontology-seed",
                        file_path=f"seed/{entry.adapter_id}.txt",
                        language_id=entry.adapter_id.split("_", 1)[0],
                        cursor_line=0,
                        cursor_column=0,
                        symbols_in_scope=[entry.adapter_id, *entry.keywords[:2]],
                        metadata={
                            "query": entry.description,
                            "semantic_context": " ".join(entry.keywords),
                            "code_block": " ".join(entry.keywords),
                        },
                    )
                )
                class_document_weights[entry.adapter_id] += 1.0
                class_token_weights[entry.adapter_id].update(tokens)
                vocabulary.update(tokens)

        adapters = sorted(set(class_document_weights) | {self._fallback_adapter})
        for adapter in adapters:
            class_document_weights.setdefault(adapter, 0.0)
            class_token_weights.setdefault(adapter, Counter())

        model = LearnedRouterModel(
            adapters=adapters,
            fallback_adapter=self._fallback_adapter,
            class_document_weights=dict(class_document_weights),
            class_token_totals={
                adapter: float(sum(counter.values())) for adapter, counter in class_token_weights.items()
            },
            token_weights={
                adapter: {token: float(weight) for token, weight in counter.items()}
                for adapter, counter in class_token_weights.items()
            },
            vocabulary=sorted(vocabulary),
            trained_rows=row_count,
            metadata={
                "source_paths": source_paths or [],
                "augment_with_ontology": augment_with_ontology,
            },
        )
        return model

    def train_from_paths(
        self,
        paths: list[str | Path],
        *,
        augment_with_ontology: bool = True,
    ) -> LearnedRouterModel:
        rows = self.load_rows(paths)
        return self.train(
            rows,
            augment_with_ontology=augment_with_ontology,
            source_paths=[str(Path(path)) for path in paths],
        )

    def evaluate_rows(self, rows: list[dict[str, Any]], router: LearnedRouter) -> dict[str, float | int]:
        total = 0
        correct = 0.0
        for row in rows:
            event = TelemetryEvent.model_validate(row["event"])
            decision = router.predict(event)
            correct += self._score_prediction(row, decision.adapter_id)
            total += 1

        accuracy = (correct / total) if total else 0.0
        return {
            "events_processed": total,
            "top1_accuracy": accuracy,
        }

    def _label_weights(self, row: dict[str, Any]) -> dict[str, float]:
        label = row.get("expected_label")
        if isinstance(label, dict):
            weights: dict[str, float] = {}
            primary = ensure_known_adapter(str(label.get("primary_adapter", self._fallback_adapter)).strip())
            weights[primary] = 1.0
            alternatives = label.get("acceptable_alternatives", [])
            if isinstance(alternatives, list):
                for alternative in alternatives:
                    normalized = ensure_known_adapter(str(alternative).strip())
                    if normalized and normalized != primary:
                        weights[normalized] = max(weights.get(normalized, 0.0), 0.35)
            return weights

        expected_adapter = str(row.get("expected_adapter", self._fallback_adapter)).strip() or self._fallback_adapter
        normalized = ensure_known_adapter(expected_adapter)
        return {normalized: 1.0}

    def _score_prediction(self, row: dict[str, Any], predicted_adapter: str) -> float:
        label = row.get("expected_label")
        if isinstance(label, dict):
            primary = str(label.get("primary_adapter", self._fallback_adapter)).strip() or self._fallback_adapter
            alternatives = {
                str(item).strip() for item in label.get("acceptable_alternatives", []) if str(item).strip()
            } if isinstance(label.get("acceptable_alternatives", []), list) else set()
            if predicted_adapter == primary:
                return 1.0
            if predicted_adapter in alternatives:
                return 0.5
            return 0.0

        expected_adapter = str(row.get("expected_adapter", self._fallback_adapter)).strip() or self._fallback_adapter
        return 1.0 if predicted_adapter == expected_adapter else 0.0
