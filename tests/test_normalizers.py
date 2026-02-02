import asyncio

from intent_cache_agent.normalizers import AdkLlmNormalizer


def test_adk_llm_normalizer_parses_json() -> None:
    def run_agent(text, context):
        return "{" + '"intent":"faq","slots":{},"meta":null' + "}"

    normalizer = AdkLlmNormalizer(run_agent=run_agent)
    result = normalizer.normalize("help", None)
    assert result is not None
    assert result.intent == "faq"


def test_adk_llm_normalizer_parses_dict() -> None:
    def run_agent(text, context):
        return {"intent": "faq", "slots": {"topic": "general"}}

    normalizer = AdkLlmNormalizer(run_agent=run_agent)
    result = normalizer.normalize("help", None)
    assert result is not None
    assert result.slots["topic"] == "general"


def test_adk_llm_normalizer_async() -> None:
    async def run_agent(text, context):
        return {"intent": "faq", "slots": {}}

    normalizer = AdkLlmNormalizer(run_agent=run_agent)
    result = asyncio.run(normalizer.normalize_async("help", None))
    assert result is not None
    assert result.intent == "faq"
