from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel, Field

from backend.labeling.ontology import ADAPTER_ONTOLOGY, ensure_known_adapter, list_adapter_ids


class AdapterLabel(BaseModel):
    primary_adapter: str
    acceptable_alternatives: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str


class LabelProvider(Protocol):
    def label(self, *, code_block: str, symbols: list[str], metadata: dict) -> AdapterLabel:
        ...


@dataclass(slots=True)
class HeuristicLabelProvider:
    """Deterministic local provider used before external LLM provider integration."""

    default_adapter: str = "general"

    def label(self, *, code_block: str, symbols: list[str], metadata: dict) -> AdapterLabel:
        haystack = " ".join([code_block, " ".join(symbols), json.dumps(metadata)]).lower()

        ranked: list[tuple[str, int]] = []
        for entry in ADAPTER_ONTOLOGY:
            score = sum(1 for keyword in entry.keywords if keyword.lower() in haystack)
            ranked.append((entry.adapter_id, score))

        ranked.sort(key=lambda x: x[1], reverse=True)
        top_adapter, top_score = ranked[0]

        if top_score == 0:
            top_adapter = self.default_adapter

        alternatives = [name for name, score in ranked[1:4] if score > 0 and name != top_adapter]
        confidence = 0.45 if top_score == 0 else min(0.95, 0.55 + (top_score * 0.08))

        return AdapterLabel(
            primary_adapter=ensure_known_adapter(top_adapter),
            acceptable_alternatives=[ensure_known_adapter(name) for name in alternatives],
            confidence=confidence,
            reasoning="heuristic keyword alignment",
        )


def parse_structured_label(raw_json: str) -> AdapterLabel:
    payload = json.loads(raw_json)
    label = AdapterLabel.model_validate(payload)

    ensure_known_adapter(label.primary_adapter)
    for adapter in label.acceptable_alternatives:
        ensure_known_adapter(adapter)

    if label.primary_adapter in label.acceptable_alternatives:
        label.acceptable_alternatives = [
            item for item in label.acceptable_alternatives if item != label.primary_adapter
        ]

    return label


def annotate_compiled_rows(rows: list[dict], provider: LabelProvider | None = None) -> list[dict]:
    provider = provider or HeuristicLabelProvider()
    known = set(list_adapter_ids())
    annotated: list[dict] = []

    for row in rows:
        event = dict(row.get("event", {}))
        metadata = dict(event.get("metadata", {}))
        code_block = str(metadata.get("code_block", ""))
        symbols = [str(item) for item in event.get("symbols_in_scope", [])]

        label = provider.label(code_block=code_block, symbols=symbols, metadata=metadata)
        if label.primary_adapter not in known:
            raise ValueError(f"Provider returned unknown primary adapter: {label.primary_adapter}")

        enriched = dict(row)
        enriched["expected_label"] = label.model_dump(mode="json")
        enriched["expected_adapter"] = label.primary_adapter
        enriched["label_status"] = "auto_labeled"

        event["metadata"] = {
            **metadata,
            "label_status": "auto_labeled",
            "label_confidence": label.confidence,
            "label_reasoning": label.reasoning,
        }
        enriched["event"] = event

        annotated.append(enriched)

    return annotated
