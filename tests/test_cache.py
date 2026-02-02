import time

from intent_cache_agent.cache import InMemoryExactCache, InMemorySemanticCache
from intent_cache_agent.models import Artifact


def test_inmemory_exact_cache_ttl(monkeypatch) -> None:
    cache = InMemoryExactCache()
    artifact = Artifact(
        type="intent_cache",
        payload={"answer": "ok"},
        version="v1",
        scope={},
        ttl_seconds=10,
    )

    monkeypatch.setattr(time, "time", lambda: 1000.0)
    cache.set("key", artifact)
    assert cache.get("key") is not None

    monkeypatch.setattr(time, "time", lambda: 1011.0)
    assert cache.get("key") is None


def test_inmemory_semantic_cache_search() -> None:
    def embedder(intent, slots):
        return [1.0, 0.0] if intent == "faq" else [0.0, 1.0]

    cache = InMemorySemanticCache(embedder=embedder)
    artifact_a = Artifact(
        type="intent_cache",
        payload={"answer": "a"},
        version="v1",
        scope={},
        ttl_seconds=3600,
    )
    artifact_b = Artifact(
        type="intent_cache",
        payload={"answer": "b"},
        version="v1",
        scope={},
        ttl_seconds=3600,
    )

    cache.add([1.0, 0.0], artifact_a)
    cache.add([0.0, 1.0], artifact_b)

    result = cache.search([1.0, 0.0], min_score=0.5)
    assert result is not None
    assert result[0].payload["answer"] == "a"
