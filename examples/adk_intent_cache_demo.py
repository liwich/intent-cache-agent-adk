import asyncio
import json
from typing import Optional

# Requires: pip install "intent-cache-agent[adk]" and a valid Gemini API key.

from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from intent_cache_agent.adk_agent import IntentCacheAgent
from intent_cache_agent.adk_tool import build_agent_tool
from intent_cache_agent.cache import InMemoryExactCache
from intent_cache_agent.core import CachedIntentAgent
from intent_cache_agent.key_builder import build_cache_key
from intent_cache_agent.models import Artifact, CacheOptions
from intent_cache_agent.normalizers import AdkLlmNormalizer
from intent_cache_agent.registry import SimpleIntentRegistry


class NormalizedOutput(BaseModel):
    intent: str = Field(description="Allowed intents: faq")
    slots: dict = Field(default_factory=dict)
    meta: Optional[dict] = None


def _extract_text(events) -> Optional[str]:
    for event in reversed(events):
        content = getattr(event, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if not parts:
            continue
        for part in parts:
            text = getattr(part, "text", None)
            if text:
                return text
    return None


def _build_normalizer_agent() -> LlmAgent:
    return LlmAgent(
        name="intent_normalizer",
        model="gemini-2.5-flash",
        include_contents="none",
        instruction=(
            "You are a deterministic normalizer. "
            "Return JSON that matches the schema. "
            "Allowed intents: faq. "
            "If the request is a help or faq request, return intent='faq'. "
            "Otherwise return intent='unknown' with empty slots."
        ),
        output_schema=NormalizedOutput,
        generate_content_config=types.GenerateContentConfig(temperature=0),
    )


async def _run_normalizer(normalizer_agent: LlmAgent, text: str) -> Optional[str]:
    runner = InMemoryRunner(agent=normalizer_agent)
    events = await runner.run_debug(text)
    return _extract_text(events)


def main() -> None:
    normalizer_agent = _build_normalizer_agent()
    async def run_agent(text: str, context: Optional[dict]) -> Optional[str]:
        return await _run_normalizer(normalizer_agent, text)

    normalizer = AdkLlmNormalizer(run_agent=run_agent)

    registry = SimpleIntentRegistry(allowed_intents={"faq"})
    exact_cache = InMemoryExactCache()
    options = CacheOptions(scope={"tenant": "demo"})
    cached_agent = CachedIntentAgent(
        normalizer=normalizer,
        registry=registry,
        exact_cache=exact_cache,
        default_options=options,
    )

    artifact = Artifact(
        type="intent_cache",
        payload={"answer": "Cached FAQ response."},
        version="v1",
        scope={"tenant": "demo"},
        ttl_seconds=3600,
    )

    key = build_cache_key(
        intent="faq",
        slots={},
        scope={"tenant": "demo"},
        artifact_type=options.artifact_type,
        schema_version=options.schema_version,
    )
    exact_cache.set(key, artifact)

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

    runner = InMemoryRunner(agent=root_agent)
    events = asyncio.run(runner.run_debug("help"))
    final_text = _extract_text(events)
    print(json.dumps({"response": final_text}, ensure_ascii=True))


if __name__ == "__main__":
    main()
