from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class NormalizedIntent:
    intent: str
    slots: Dict[str, Any] = field(default_factory=dict)
    meta: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class Artifact:
    type: str
    payload: Any
    version: str | int
    scope: Dict[str, Any]
    ttl_seconds: int
    provenance: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CacheOptions:
    enable_semantic: bool = False
    min_score: float = 0.85
    cache_bypass: bool = False
    artifact_type: str = "intent_cache"
    schema_version: str = "v1"
    scope: Optional[Dict[str, Any]] = None
