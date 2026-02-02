from intent_cache_agent.cache import InMemoryExactCache
from intent_cache_agent.core import CachedIntentAgent
from intent_cache_agent.models import Artifact, CacheOptions
from intent_cache_agent.key_builder import build_cache_key
from intent_cache_agent.normalizers import RuleBasedNormalizer
from intent_cache_agent.registry import SimpleIntentRegistry


def main() -> None:
    registry = SimpleIntentRegistry(allowed_intents={"faq", "status"})
    normalizer = RuleBasedNormalizer({"help": "faq", "status": "status"})
    exact_cache = InMemoryExactCache()

    cached_agent = CachedIntentAgent(
        normalizer=normalizer,
        registry=registry,
        exact_cache=exact_cache,
    )

    artifact = Artifact(
        type="intent_cache",
        payload={"answer": "Here are the FAQs."},
        version="v1",
        scope={"tenant": "demo"},
        ttl_seconds=3600,
    )

    options = CacheOptions(scope={"tenant": "demo"})
    key = build_cache_key(
        intent="faq",
        slots={},
        scope={"tenant": "demo"},
        artifact_type=options.artifact_type,
        schema_version=options.schema_version,
    )
    exact_cache.set(key, artifact)

    result = cached_agent.lookup("help", context={"tenant": "demo"}, options=options)
    print(result)


if __name__ == "__main__":
    main()
