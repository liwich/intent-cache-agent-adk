from __future__ import annotations

import inspect
from dataclasses import replace
from typing import Any, Awaitable, Dict, Optional, cast

from .canonicalization import DefaultCanonicalizer
from .interfaces import Canonicalizer, ExactCache, IntentRegistry, Normalizer, SemanticCache
from .key_builder import build_cache_key
from .models import Artifact, CacheOptions, NormalizedIntent


class CachedIntentAgent:
    def __init__(
        self,
        *,
        normalizer: Normalizer,
        canonicalizer: Canonicalizer = DefaultCanonicalizer(),
        registry: IntentRegistry,
        exact_cache: ExactCache,
        semantic_cache: Optional[SemanticCache] = None,
        default_options: Optional[CacheOptions] = None,
    ) -> None:
        self._normalizer = normalizer
        self._canonicalizer = canonicalizer
        self._registry = registry
        self._exact_cache = exact_cache
        self._semantic_cache = semantic_cache
        self._default_options = default_options or CacheOptions()

    def lookup(
        self,
        text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[CacheOptions] = None,
    ) -> Optional[Artifact]:
        resolved = options or self._default_options
        if resolved.cache_bypass:
            return None
        normalized = self._normalizer.normalize(text, context)
        if inspect.isawaitable(normalized):
            raise RuntimeError("Async normalizer detected. Use lookup_async instead.")
        if not normalized:
            return None

        if not self._registry.is_allowed(normalized.intent):
            return None
        if not self._registry.validate_slots(normalized.intent, normalized.slots):
            return None

        canonical = self._canonicalizer.canonicalize(normalized.intent, normalized.slots)
        key = build_cache_key(
            intent=canonical.intent,
            slots=canonical.slots,
            scope=resolved.scope or context,
            artifact_type=resolved.artifact_type,
            schema_version=resolved.schema_version,
        )

        exact_hit = self._exact_cache.get(key)
        if exact_hit:
            return _with_provenance(exact_hit, source="cache", key=key, score=None)

        if not resolved.enable_semantic or self._semantic_cache is None:
            return None

        vector = self._semantic_cache.embed(canonical.intent, canonical.slots)
        semantic_hit = self._semantic_cache.search(vector, resolved.min_score)
        if not semantic_hit:
            return None

        artifact, score = semantic_hit
        return _with_provenance(artifact, source="semantic", key=key, score=score)

    async def lookup_async(
        self,
        text: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[CacheOptions] = None,
    ) -> Optional[Artifact]:
        resolved = options or self._default_options
        if resolved.cache_bypass:
            return None

        normalized = await _normalize_async(self._normalizer, text, context)
        if not normalized:
            return None

        if not self._registry.is_allowed(normalized.intent):
            return None
        if not self._registry.validate_slots(normalized.intent, normalized.slots):
            return None

        canonical = self._canonicalizer.canonicalize(normalized.intent, normalized.slots)
        key = build_cache_key(
            intent=canonical.intent,
            slots=canonical.slots,
            scope=resolved.scope or context,
            artifact_type=resolved.artifact_type,
            schema_version=resolved.schema_version,
        )

        exact_hit = self._exact_cache.get(key)
        if exact_hit:
            return _with_provenance(exact_hit, source="cache", key=key, score=None)

        if not resolved.enable_semantic or self._semantic_cache is None:
            return None

        vector = self._semantic_cache.embed(canonical.intent, canonical.slots)
        semantic_hit = self._semantic_cache.search(vector, resolved.min_score)
        if not semantic_hit:
            return None

        artifact, score = semantic_hit
        return _with_provenance(artifact, source="semantic", key=key, score=score)


def _with_provenance(artifact: Artifact, *, source: str, key: str, score: Optional[float]) -> Artifact:
    provenance = dict(artifact.provenance) if artifact.provenance else {}
    provenance.update({"source": source, "key": key, "score": score})
    return replace(artifact, provenance=provenance)


async def _normalize_async(normalizer: Any, text: str, context: Optional[Dict[str, Any]]):
    normalize_async = getattr(normalizer, "normalize_async", None)
    if callable(normalize_async):
        result = normalize_async(text, context)
        if inspect.isawaitable(result):
            return await cast(Awaitable[Any], result)
        return result
    result: Any = normalizer.normalize(text, context)
    if inspect.isawaitable(result):
        return await cast(Awaitable[Any], result)
    return result
