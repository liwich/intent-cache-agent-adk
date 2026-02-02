from intent_cache_agent.cache import InMemoryExactCache
from intent_cache_agent.core import CachedIntentAgent
from intent_cache_agent.key_builder import build_cache_key
from intent_cache_agent.models import Artifact, CacheOptions, NormalizedIntent
from intent_cache_agent.registry import SimpleIntentRegistry


class SqlRuleNormalizer:
    def __init__(self) -> None:
        self._patterns = {
            "total sales by region": {
                "metric": "total_sales",
                "dimension": "region",
                "table": "sales",
            },
            "daily active users": {
                "metric": "daily_active_users",
                "dimension": "date",
                "table": "events",
            },
            "orders last 7 days": {
                "metric": "orders",
                "dimension": "date",
                "time_range": "last_7_days",
                "table": "orders",
            },
        }

    def normalize(self, text: str, context=None):
        lowered = text.lower().strip()
        for phrase, slots in self._patterns.items():
            if phrase in lowered:
                return NormalizedIntent(intent="sql_query", slots=slots, meta={"matched": phrase})
        return None


def seed_sql_cache(cache: InMemoryExactCache, options: CacheOptions) -> None:
    artifacts = [
        (
            {"metric": "total_sales", "dimension": "region", "table": "sales"},
            "SELECT region, SUM(amount) AS total_sales FROM sales GROUP BY region;",
        ),
        (
            {"metric": "daily_active_users", "dimension": "date", "table": "events"},
            "SELECT event_date AS date, COUNT(DISTINCT user_id) AS daily_active_users "
            "FROM events GROUP BY event_date;",
        ),
        (
            {
                "metric": "orders",
                "dimension": "date",
                "time_range": "last_7_days",
                "table": "orders",
            },
            "SELECT order_date AS date, COUNT(*) AS orders "
            "FROM orders WHERE order_date >= CURRENT_DATE - INTERVAL '7 day' "
            "GROUP BY order_date;",
        ),
    ]

    for slots, sql in artifacts:
        key = build_cache_key(
            intent="sql_query",
            slots=slots,
            scope=options.scope,
            artifact_type=options.artifact_type,
            schema_version=options.schema_version,
        )
        artifact = Artifact(
            type=options.artifact_type,
            payload={"sql": sql},
            version=options.schema_version,
            scope=options.scope or {},
            ttl_seconds=3600,
        )
        cache.set(key, artifact)


def main() -> None:
    registry = SimpleIntentRegistry(
        allowed_intents={"sql_query"},
        allowed_slots={
            "sql_query": {"metric", "dimension", "time_range", "table"},
        },
    )

    normalizer = SqlRuleNormalizer()
    exact_cache = InMemoryExactCache()
    options = CacheOptions(scope={"tenant": "analytics"})

    seed_sql_cache(exact_cache, options)

    cached_agent = CachedIntentAgent(
        normalizer=normalizer,
        registry=registry,
        exact_cache=exact_cache,
        default_options=options,
    )

    prompts = [
        "Show total sales by region",
        "We need daily active users",
        "Give me orders last 7 days",
        "How many refunds happened yesterday?",
    ]

    for prompt in prompts:
        result = cached_agent.lookup(prompt)
        if result is None:
            print(f"MISS: {prompt}")
        else:
            sql = result.payload.get("sql")
            print(f"HIT: {prompt}\n  SQL: {sql}")


if __name__ == "__main__":
    main()
