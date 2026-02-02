from intent_cache_agent.key_builder import build_cache_key


def test_build_cache_key_deterministic() -> None:
    key_a = build_cache_key(
        intent="faq",
        slots={"b": 2, "a": 1},
        scope={"tenant": "demo", "env": "dev"},
        artifact_type="intent_cache",
        schema_version="v1",
    )
    key_b = build_cache_key(
        intent="faq",
        slots={"a": 1, "b": 2},
        scope={"env": "dev", "tenant": "demo"},
        artifact_type="intent_cache",
        schema_version="v1",
    )

    assert key_a == key_b
