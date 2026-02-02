from __future__ import annotations

import inspect
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

from .models import NormalizedIntent


@dataclass
class RuleBasedNormalizer:
    intent_map: Dict[str, str]

    def normalize(self, text: str, context: Dict[str, Any] | None) -> Optional[NormalizedIntent]:
        lowered = text.lower()
        for keyword, intent in self.intent_map.items():
            if keyword in lowered:
                return NormalizedIntent(intent=intent, slots={}, meta={"matched": keyword})
        return None


class CallableNormalizer:
    def __init__(self, fn: Callable[[str, Optional[Dict[str, Any]]], Optional[NormalizedIntent]]) -> None:
        self._fn = fn

    def normalize(self, text: str, context: Dict[str, Any] | None) -> Optional[NormalizedIntent]:
        return self._fn(text, context)


class AdkLlmNormalizer:
    """Adapter for ADK-based LLM normalization.

    Provide a run_agent callable that executes the LLM agent and returns
    a JSON string or dict matching the NormalizedIntent schema.
    """

    def __init__(
        self,
        *,
        run_agent: Callable[
            [str, Optional[Dict[str, Any]]], Optional[dict | str] | Awaitable[Optional[dict | str]]
        ],
    ) -> None:
        self._run_agent = run_agent

    def normalize(self, text: str, context: Dict[str, Any] | None) -> Optional[NormalizedIntent]:
        result = self._run_agent(text, context)
        if inspect.isawaitable(result):
            raise RuntimeError("Async run_agent detected. Use normalize_async instead.")
        return _parse_normalized(result)

    async def normalize_async(
        self, text: str, context: Dict[str, Any] | None
    ) -> Optional[NormalizedIntent]:
        result = self._run_agent(text, context)
        if inspect.isawaitable(result):
            result = await result
        return _parse_normalized(result)


def _parse_normalized(result: Optional[dict | str]) -> Optional[NormalizedIntent]:
        if result is None:
            return None
        if isinstance(result, str):
            try:
                payload = json.loads(result)
            except json.JSONDecodeError:
                return None
        else:
            payload = result
        if not isinstance(payload, dict):
            return None
        intent = payload.get("intent")
        slots = payload.get("slots", {})
        meta = payload.get("meta")
        if not isinstance(intent, str) or not isinstance(slots, dict):
            return None
        return NormalizedIntent(intent=intent, slots=slots, meta=meta)
