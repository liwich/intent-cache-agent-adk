from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict

from .models import NormalizedIntent


def _normalize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (list, tuple)):
        return [_normalize_value(item) for item in value if item is not None]
    if isinstance(value, dict):
        return {key: _normalize_value(value[key]) for key in sorted(value)}
    return str(value)


def canonicalize_mapping(mapping: Dict[str, Any], drop_empty: bool = True) -> Dict[str, Any]:
    canonical: Dict[str, Any] = {}
    for key in sorted(mapping):
        normalized = _normalize_value(mapping[key])
        if drop_empty and _is_empty(normalized):
            continue
        canonical[key] = normalized
    return canonical


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if value == "":
        return True
    if value == []:
        return True
    if value == {}:
        return True
    return False


def default_canonicalizer(intent: str, slots: Dict[str, Any]) -> NormalizedIntent:
    return NormalizedIntent(intent=intent, slots=canonicalize_mapping(slots))


class DefaultCanonicalizer:
    def canonicalize(self, intent: str, slots: Dict[str, Any]) -> NormalizedIntent:
        return default_canonicalizer(intent, slots)
