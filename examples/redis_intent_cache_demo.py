import redis

from intent_cache_agent.core import CachedIntentAgent
from intent_cache_agent.key_builder import build_cache_key
from intent_cache_agent.models import Artifact, CacheOptions, NormalizedIntent
from intent_cache_agent.redis_cache import RedisExactCache
from intent_cache_agent.registry import SimpleIntentRegistry


class SimpleNormalizer:
    def normalize(self, text: str, context=None):
        lowered = text.lower()
        if "help" in lowered:
            return NormalizedIntent(intent="faq", slots={"topic": "general"}, meta=None)
        return None


def main() -> None:
    client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    cache = RedisExactCache(client)

    registry = SimpleIntentRegistry(
        allowed_intents={"faq"},
        allowed_slots={"faq": {"topic"}},
    )

    options = CacheOptions(scope={"tenant": "demo"})
    cached_agent = CachedIntentAgent(
        normalizer=SimpleNormalizer(),
        registry=registry,
        exact_cache=cache,
        default_options=options,
    )

    key = build_cache_key(
        intent="faq",
        slots={"topic": "general"},
        scope=options.scope,
        artifact_type=options.artifact_type,
        schema_version=options.schema_version,
    )
    artifact = Artifact(
        type=options.artifact_type,
        payload={"answer": "This is cached in Redis."},
        version=options.schema_version,
        scope=options.scope or {},
        ttl_seconds=300,
    )
    cache.set(key, artifact)

    result = cached_agent.lookup("help")
    print(result)


if __name__ == "__main__":
    main()
