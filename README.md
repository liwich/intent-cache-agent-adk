# Intent Cache Agent (ADK + Gemini)

Reusable intent-cache agent that works as an ADK agent-as-tool. It normalizes a request into `{intent, slots}`, checks the cache (exact first, semantic optional), and returns a cached artifact or `null`.

## Why this exists

Teams keep re-solving the same problem: repeated user requests that map to the same intent and parameters still hit expensive LLM/tool pipelines. This project provides a reusable, deterministic cache layer that short-circuits those repeats without changing downstream agents.

What it solves:
- **Latency**: repeated intents return cached artifacts immediately.
- **Cost**: avoid LLM/tool invocations for common, stable requests.
- **Consistency**: canonical keys + strict normalization reduce drift.
- **Reusability**: teams plug in their own intents/slots and backends.

Where it fits:
- Sits before reasoning agents as an **agent-as-tool**.
- Returns a cached artifact or `null` so the existing flow remains unchanged.

## Install

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e .
```

For ADK + Gemini support:

```bash
.venv\Scripts\python.exe -m pip install "intent-cache-agent[adk]"
```

## Environment

Copy `.env.example` to `.env` and set credentials.

```text
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

## Local services (Docker)

If you want Redis for the Redis demo, start it with Docker Compose:

```bash
docker compose up -d
```

## Agent-as-Tool usage (ADK)

The cached agent is wrapped with `AgentTool` and called before any reasoning agent.

```python
from google.adk.agents import LlmAgent
from intent_cache_agent.adk_agent import IntentCacheAgent
from intent_cache_agent.adk_tool import build_agent_tool
from intent_cache_agent.core import CachedIntentAgent
from intent_cache_agent.cache import InMemoryExactCache
from intent_cache_agent.registry import SimpleIntentRegistry
from intent_cache_agent.normalizers import RuleBasedNormalizer

registry = SimpleIntentRegistry(allowed_intents={"faq"})
normalizer = RuleBasedNormalizer({"help": "faq"})
cache = InMemoryExactCache()

cached_agent = CachedIntentAgent(
    normalizer=normalizer,
    registry=registry,
    exact_cache=cache,
)

intent_cache_agent = IntentCacheAgent(name="intent_cache_agent", cached_agent=cached_agent)
intent_cache_tool = build_agent_tool(intent_cache_agent, skip_summarization=True)

root_agent = LlmAgent(
    name="root_agent",
    model="gemini-2.5-flash",
    instruction=(
        "Call the intent_cache_agent tool first. "
        "If it returns null, answer normally. "
        "If it returns an artifact JSON, respond with payload.answer only."
    ),
    tools=[intent_cache_tool],
)
```

## Execution flow (what happens at runtime)

1. User request enters the root agent.
2. Root agent calls `intent_cache_agent` tool first.
3. Cache agent normalizes text into `{intent, slots}`.
4. Intent/slot allowlist is validated.
5. Canonical key is built from `intent + slots + scope + schema_version`.
6. Exact cache lookup is attempted.
7. If exact hit → return cached artifact JSON.
8. If exact miss and semantic enabled → embed + vector search.
9. If semantic hit → return cached artifact JSON.
10. If miss → return `null`, root agent proceeds with normal reasoning.

## Demos

- Basic cache hit: `examples/basic_usage.py`
- ADK + Gemini Flash tool demo: `examples/adk_intent_cache_demo.py`
- SQL intent cache demo (seeded queries): `examples/sql_intent_cache_demo.py`
- Redis exact-cache demo (optional): `examples/redis_intent_cache_demo.py`

Run a demo (Windows):

```bash
.venv\Scripts\python.exe examples\sql_intent_cache_demo.py
```

Run a demo (macOS/Linux):

```bash
.venv/bin/python examples/sql_intent_cache_demo.py
```

For Redis demo:

```bash
.venv\Scripts\python.exe -m pip install "intent-cache-agent[redis]"
.venv\Scripts\python.exe examples\redis_intent_cache_demo.py
```

## Tests

```bash
.venv\Scripts\python.exe -m pip install "intent-cache-agent[dev]"
.venv\Scripts\python.exe -m pytest
```

## Extension points

- **Normalizer**: swap in a Gemini normalizer (`AdkLlmNormalizer`) or rules.
- **Intent registry**: define your allowed intents/slots.
- **Cache backends**: swap the in-memory cache for Redis/DB. `RedisExactCache` lives in `src/intent_cache_agent/redis_cache.py` and is shown in `examples/redis_intent_cache_demo.py`.
- **Semantic cache**: optional; use vector search if needed.

## Project layout

- `src/intent_cache_agent/core.py` – cache flow (exact → semantic)
- `src/intent_cache_agent/adk_agent.py` – ADK agent wrapper
- `src/intent_cache_agent/normalizers.py` – rule-based + ADK normalizer adapters
- `src/intent_cache_agent/cache.py` – in-memory cache backends
- `REFERENCE-IMPLEMENTATION-intent-cache-agent.md` – full spec

## Seeding the cache

The cache expects a deterministic key built from `{intent, slots, scope, schema_version}`. Use the key builder and store an artifact.

```python
from intent_cache_agent.cache import InMemoryExactCache
from intent_cache_agent.key_builder import build_cache_key
from intent_cache_agent.models import Artifact, CacheOptions

cache = InMemoryExactCache()
options = CacheOptions(scope={"tenant": "demo"})

key = build_cache_key(
    intent="faq",
    slots={"topic": "billing"},
    scope=options.scope,
    artifact_type=options.artifact_type,
    schema_version=options.schema_version,
)

artifact = Artifact(
    type=options.artifact_type,
    payload={"answer": "Billing FAQs..."},
    version=options.schema_version,
    scope=options.scope or {},
    ttl_seconds=3600,
)

cache.set(key, artifact)
```
