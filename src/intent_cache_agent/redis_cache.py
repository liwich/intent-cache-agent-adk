from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, cast

import redis

from .models import Artifact


class RedisExactCache:
    def __init__(self, client: redis.Redis, prefix: str = "intent_cache:") -> None:
        self._client = client
        self._prefix = prefix

    def get(self, key: str) -> Artifact | None:
        raw = self._client.get(self._prefix + key)
        if not raw:
            return None
        raw_text = cast(Any, raw)
        if not isinstance(raw_text, str):
            raw_text = raw_text.decode("utf-8")
        payload = json.loads(raw_text)
        return Artifact(**payload)

    def set(self, key: str, artifact: Artifact, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else artifact.ttl_seconds
        raw = json.dumps(asdict(artifact), ensure_ascii=True)
        if ttl:
            self._client.setex(self._prefix + key, ttl, raw)
        else:
            self._client.set(self._prefix + key, raw)
