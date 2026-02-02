from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from .models import Artifact, NormalizedIntent


class Normalizer(Protocol):
    def normalize(self, text: str, context: Dict[str, Any] | None) -> Optional[NormalizedIntent]: ...


class Canonicalizer(Protocol):
    def canonicalize(self, intent: str, slots: Dict[str, Any]) -> NormalizedIntent: ...


class IntentRegistry(Protocol):
    def is_allowed(self, intent: str) -> bool: ...

    def validate_slots(self, intent: str, slots: Dict[str, Any]) -> bool: ...


class ExactCache(Protocol):
    def get(self, key: str) -> Optional[Artifact]: ...

    def set(self, key: str, artifact: Artifact, ttl_seconds: Optional[int] = None) -> None: ...


class SemanticCache(Protocol):
    def embed(self, intent: str, slots: Dict[str, Any]) -> list[float]: ...

    def search(self, vector: list[float], min_score: float) -> Optional[tuple[Artifact, float]]: ...
