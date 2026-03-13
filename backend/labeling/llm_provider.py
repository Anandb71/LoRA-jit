from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field

import httpx

from backend.labeling.auto_labeler import AdapterLabel, HeuristicLabelProvider, parse_structured_label
from backend.labeling.ontology import ontology_prompt_block

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """\
You are an expert code-context classifier for a LoRA adapter routing system.

Your task: given a code snippet and its semantic context, identify the most appropriate
LoRA adapter to activate for the next generation step.

{ontology_block}

Respond ONLY with a single JSON object in this exact schema (no markdown fences):
{{
  "primary_adapter": "<adapter_id>",
  "acceptable_alternatives": ["<adapter_id>", ...],
  "confidence": <float 0.0-1.0>,
  "reasoning": "<one sentence>"
}}

Rules:
- primary_adapter MUST be one of the allowed adapter IDs above.
- acceptable_alternatives may be empty but every entry must also be an allowed adapter ID.
- Never return adapter IDs not in the allowed list.
- confidence reflects how certain you are; use < 0.6 for ambiguous cases.
"""

_USER_PROMPT_TEMPLATE = """\
Code block:
```
{code_block}
```

Active symbols: {symbols}
File metadata: {metadata}

Classify the adapter.
"""


@dataclass
class LlmLabelProvider:
    """OpenAI-compatible HTTP label provider.

    Falls back silently to :class:`HeuristicLabelProvider` on any network or
    parsing error so that the annotation pipeline never hard-fails.

    Parameters
    ----------
    model:
        The model identifier sent to the API (e.g. ``"gpt-4o-mini"``).
    api_base:
        Base URL for the OpenAI-compatible endpoint.
        Defaults to the ``LORA_JIT_LLM_API_BASE`` env var, or OpenAI's endpoint.
    api_key:
        Bearer token for the API.
        Defaults to the ``LORA_JIT_LLM_API_KEY`` env var.
    timeout:
        HTTP timeout in seconds (default 30).
    fallback_on_error:
        When True (default), fall back to heuristic labeling on any error
        instead of raising.
    """

    model: str = "gpt-4o-mini"
    api_base: str = field(
        default_factory=lambda: os.environ.get(
            "LORA_JIT_LLM_API_BASE", "https://api.openai.com/v1"
        )
    )
    api_key: str = field(
        default_factory=lambda: os.environ.get("LORA_JIT_LLM_API_KEY", "")
    )
    timeout: float = 30.0
    fallback_on_error: bool = True

    # ------------------------------------------------------------------
    # LabelProvider protocol
    # ------------------------------------------------------------------

    def label(self, *, code_block: str, symbols: list[str], metadata: dict) -> AdapterLabel:
        try:
            return self._call_llm(code_block=code_block, symbols=symbols, metadata=metadata)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "LlmLabelProvider failed (%s: %s); falling back to heuristic.", type(exc).__name__, exc
            )
            if not self.fallback_on_error:
                raise
            return HeuristicLabelProvider().label(
                code_block=code_block, symbols=symbols, metadata=metadata
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _build_messages(self, *, code_block: str, symbols: list[str], metadata: dict) -> list[dict]:
        system_content = _SYSTEM_PROMPT_TEMPLATE.format(ontology_block=ontology_prompt_block())
        user_content = _USER_PROMPT_TEMPLATE.format(
            code_block=code_block[:4000],  # guard against token blowout
            symbols=", ".join(symbols) if symbols else "(none)",
            metadata=json.dumps({k: v for k, v in metadata.items() if k not in ("code_block",)}, default=str)[:500],
        )
        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    def _call_llm(self, *, code_block: str, symbols: list[str], metadata: dict) -> AdapterLabel:
        messages = self._build_messages(code_block=code_block, symbols=symbols, metadata=metadata)
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.0,
            "max_tokens": 256,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.api_base.rstrip('/')}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()

        data = response.json()
        raw_content: str = data["choices"][0]["message"]["content"].strip()
        return parse_structured_label(raw_content)
