from __future__ import annotations

import json
from typing import Any, Dict, Optional

from .canonicalization import canonicalize_mapping


def build_cache_key(
    *,
    intent: str,
    slots: Dict[str, Any],
    scope: Optional[Dict[str, Any]],
    artifact_type: str,
    schema_version: str,
) -> str:
    canonical_slots = canonicalize_mapping(slots)
    canonical_scope = canonicalize_mapping(scope or {}, drop_empty=False)
    slots_json = json.dumps(canonical_slots, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    scope_json = json.dumps(canonical_scope, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return (
        f"artifact={artifact_type}"
        f"|intent={intent}"
        f"|slots={slots_json}"
        f"|scope={scope_json}"
        f"|schema_v={schema_version}"
    )
