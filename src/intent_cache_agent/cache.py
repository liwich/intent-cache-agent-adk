from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .models import Artifact


@dataclass
class _CacheEntry:
    artifact: Artifact
    expires_at: Optional[float]


class InMemoryExactCache:
    def __init__(self) -> None:
        self._store: Dict[str, _CacheEntry] = {}

    def get(self, key: str) -> Optional[Artifact]:
        entry = self._store.get(key)
        if not entry:
            return None
        if entry.expires_at is not None and time.time() >= entry.expires_at:
            self._store.pop(key, None)
            return None
        return entry.artifact

    def set(self, key: str, artifact: Artifact, ttl_seconds: Optional[int] = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else artifact.ttl_seconds
        expires_at = time.time() + ttl if ttl else None
        self._store[key] = _CacheEntry(artifact=artifact, expires_at=expires_at)


@dataclass
class _SemanticEntry:
    vector: List[float]
    artifact: Artifact


class InMemorySemanticCache:
    def __init__(self, embedder: Callable[[str, Dict[str, object]], List[float]]) -> None:
        self._embedder = embedder
        self._entries: List[_SemanticEntry] = []

    def add(self, vector: List[float], artifact: Artifact) -> None:
        self._entries.append(_SemanticEntry(vector=vector, artifact=artifact))

    def embed(self, intent: str, slots: Dict[str, object]) -> List[float]:
        return self._embedder(intent, slots)

    def search(self, vector: List[float], min_score: float) -> Optional[Tuple[Artifact, float]]:
        best_score = -1.0
        best_artifact: Optional[Artifact] = None
        for entry in self._entries:
            score = _cosine_similarity(vector, entry.vector)
            if score > best_score:
                best_score = score
                best_artifact = entry.artifact
        if best_artifact is None or best_score < min_score:
            return None
        return best_artifact, best_score


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return -1.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return -1.0
    return dot / (norm_a * norm_b)
