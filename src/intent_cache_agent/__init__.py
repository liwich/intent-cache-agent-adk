from .cache import InMemoryExactCache, InMemorySemanticCache
from .cache import InMemoryExactCache, InMemorySemanticCache
from .canonicalization import DefaultCanonicalizer, canonicalize_mapping
from .core import CachedIntentAgent
from .models import Artifact, CacheOptions, NormalizedIntent
from .registry import SimpleIntentRegistry

__all__ = [
    "Artifact",
    "CachedIntentAgent",
    "InMemoryExactCache",
    "InMemorySemanticCache",
    "NormalizedIntent",
    "DefaultCanonicalizer",
    "CacheOptions",
    "SimpleIntentRegistry",
    "canonicalize_mapping",
]

try:  # optional ADK integration
    from .adk_agent import IntentCacheAgent  # type: ignore

    __all__.append("IntentCacheAgent")
except ImportError:
    pass

try:  # optional Redis cache integration
    from .redis_cache import RedisExactCache  # type: ignore

    __all__.append("RedisExactCache")
except ImportError:
    pass
