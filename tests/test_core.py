import asyncio

from intent_cache_agent.cache import InMemoryExactCache
from intent_cache_agent.core import CachedIntentAgent
from intent_cache_agent.key_builder import build_cache_key
from intent_cache_agent.models import Artifact, CacheOptions, NormalizedIntent
from intent_cache_agent.registry import SimpleIntentRegistry


class StaticNormalizer:
    def __init__(self, intent: str, slots: dict):
        self._intent = intent
        self._slots = slots

    def normalize(self, text: str, context=None):
        return NormalizedIntent(intent=self._intent, slots=self._slots, meta=None)


class AsyncNormalizer:
    async def normalize_async(self, text: str, context=None):
        return NormalizedIntent(intent="faq", slots={"topic": "general"}, meta=None)


class FakeSemanticCache:
    def __init__(self, artifact: Artifact) -> None:
        self._artifact = artifact

    def embed(self, intent: str, slots: dict):
        return [0.1]

    def search(self, vector: list[float], min_score: float):
        return self._artifact, 0.95


def test_cached_agent_exact_hit() -> None:
    registry = SimpleIntentRegistry(
        allowed_intents={"faq"},
        allowed_slots={"faq": {"topic"}},
    )
    cache = InMemoryExactCache()
    options = CacheOptions(scope={"tenant": "demo"})
    normalizer = StaticNormalizer("faq", {"topic": "general"})

    key = build_cache_key(
        intent="faq",
        slots={"topic": "general"},
        scope=options.scope,
        artifact_type=options.artifact_type,
        schema_version=options.schema_version,
    )
    artifact = Artifact(
        type=options.artifact_type,
        payload={"answer": "cached"},
        version=options.schema_version,
        scope=options.scope or {},
        ttl_seconds=3600,
    )
    cache.set(key, artifact)

    agent = CachedIntentAgent(
        normalizer=normalizer,
        registry=registry,
        exact_cache=cache,
        default_options=options,
    )

    result = agent.lookup("help")
    assert result is not None
    assert result.payload["answer"] == "cached"
    assert result.provenance["source"] == "cache"


def test_cached_agent_semantic_fallback() -> None:
    registry = SimpleIntentRegistry(allowed_intents={"faq"})
    cache = InMemoryExactCache()
    options = CacheOptions(enable_semantic=True)
    artifact = Artifact(
        type=options.artifact_type,
        payload={"answer": "semantic"},
        version=options.schema_version,
        scope={},
        ttl_seconds=3600,
    )
    semantic_cache = FakeSemanticCache(artifact)
    normalizer = StaticNormalizer("faq", {})

    agent = CachedIntentAgent(
        normalizer=normalizer,
        registry=registry,
        exact_cache=cache,
        semantic_cache=semantic_cache,
        default_options=options,
    )

    result = agent.lookup("help")
    assert result is not None
    assert result.payload["answer"] == "semantic"
    assert result.provenance["source"] == "semantic"


def test_cached_agent_cache_bypass() -> None:
    registry = SimpleIntentRegistry(allowed_intents={"faq"})
    cache = InMemoryExactCache()
    options = CacheOptions(cache_bypass=True)
    normalizer = StaticNormalizer("faq", {})

    agent = CachedIntentAgent(
        normalizer=normalizer,
        registry=registry,
        exact_cache=cache,
        default_options=options,
    )

    assert agent.lookup("help") is None


def test_cached_agent_async_lookup() -> None:
    registry = SimpleIntentRegistry(
        allowed_intents={"faq"},
        allowed_slots={"faq": {"topic"}},
    )
    cache = InMemoryExactCache()
    options = CacheOptions(scope={"tenant": "demo"})

    key = build_cache_key(
        intent="faq",
        slots={"topic": "general"},
        scope=options.scope,
        artifact_type=options.artifact_type,
        schema_version=options.schema_version,
    )
    artifact = Artifact(
        type=options.artifact_type,
        payload={"answer": "cached"},
        version=options.schema_version,
        scope=options.scope or {},
        ttl_seconds=3600,
    )
    cache.set(key, artifact)

    agent = CachedIntentAgent(
        normalizer=AsyncNormalizer(),
        registry=registry,
        exact_cache=cache,
        default_options=options,
    )

    result = asyncio.run(agent.lookup_async("help"))
    assert result is not None
    assert result.payload["answer"] == "cached"
