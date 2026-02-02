# Examples

This folder contains runnable demos that showcase how the intent cache agent can be reused across different use cases. All examples assume you created a `.venv` and installed the project.

## 1) Basic in-memory cache

- File: `examples/basic_usage.py`
- What it shows: a rule-based normalizer + in-memory cache; exact cache hit only.
- How it works:
  1. Seeds one cached artifact.
  2. Normalizes the prompt to `intent=faq`.
  3. Exact cache lookup returns the artifact.

Run:

```bash
.venv\Scripts\python.exe examples\basic_usage.py
```

## 2) ADK + Gemini Flash tool demo

- File: `examples/adk_intent_cache_demo.py`
- What it shows: an ADK agent-as-tool using Gemini Flash normalization.
- How it works:
  1. LLM normalizer outputs structured `{intent, slots}`.
  2. Cache hit returns JSON artifact.
  3. Root agent responds with cached answer.

Run (requires ADK extras + Gemini creds):

```bash
.venv\Scripts\python.exe -m pip install "intent-cache-agent[adk]"
.venv\Scripts\python.exe examples\adk_intent_cache_demo.py
```

## 3) SQL intent cache demo

- File: `examples/sql_intent_cache_demo.py`
- What it shows: seeded SQL queries keyed by intent/slots, demonstrating reuse for query caching.
- How it works:
  1. Seeds three SQL artifacts for different intents/slots.
  2. Rule-based normalizer maps prompts to `intent=sql_query` with slots.
  3. Exact cache hits print cached SQL; unmatched prompts are misses.

Run:

```bash
.venv\Scripts\python.exe examples\sql_intent_cache_demo.py
```

## 4) Redis exact cache demo

- File: `examples/redis_intent_cache_demo.py`
- What it shows: swapping the in-memory cache for Redis using `RedisExactCache`.
- How it works:
  1. Seeds a Redis cache entry with TTL.
  2. Normalizer maps the prompt to `intent=faq` and a slot.
  3. Redis returns the cached artifact.

Run (requires Redis and extras):

```bash
.venv\Scripts\python.exe -m pip install "intent-cache-agent[redis]"
docker compose up -d
.venv\Scripts\python.exe examples\redis_intent_cache_demo.py
```
