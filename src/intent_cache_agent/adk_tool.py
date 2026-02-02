from __future__ import annotations

from typing import Any


def build_agent_tool(agent: Any, *, skip_summarization: bool = True):
    """Create an ADK AgentTool wrapper with optional summarization bypass.

    This keeps the core library independent from ADK at import time.
    """

    try:
        from google.adk.tools.agent_tool import AgentTool
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError("google-adk is required for AgentTool integration") from exc

    return AgentTool(agent=agent, skip_summarization=skip_summarization)
