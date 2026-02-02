from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, AsyncGenerator, Dict, Optional

from google.adk.agents import BaseAgent
from google.adk.events import Event
from google.genai import types

from .core import CachedIntentAgent


class IntentCacheAgent(BaseAgent):
    cached_agent: CachedIntentAgent
    model_config = {"arbitrary_types_allowed": True}

    def __init__(
        self,
        *,
        name: str,
        cached_agent: CachedIntentAgent,
        description: str = "Returns cached artifacts or null.",
    ) -> None:
        super().__init__(name=name, description=description, sub_agents=[])
        self.cached_agent = cached_agent

    async def _run_async_impl(self, ctx) -> AsyncGenerator[Event, None]:
        text = _content_to_text(getattr(ctx, "user_content", None))
        context = _extract_context(ctx)
        result = await self.cached_agent.lookup_async(text, context=context)
        payload = "null" if result is None else json.dumps(asdict(result), ensure_ascii=True)
        content = types.Content(parts=[types.Part(text=payload)], role="model")
        yield Event(author=self.name, content=content)


def _content_to_text(content: Optional[types.Content]) -> str:
    if content is None or not content.parts:
        return ""
    for part in content.parts:
        text = getattr(part, "text", None)
        if text:
            return text
    return ""


def _extract_context(ctx: Any) -> Optional[Dict[str, Any]]:
    session = getattr(ctx, "session", None)
    state = getattr(session, "state", None)
    if isinstance(state, dict):
        return state.get("cache_context")
    return None
