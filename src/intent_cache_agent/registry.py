from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, Optional, Set


SlotValidator = Callable[[Dict[str, object]], bool]


@dataclass
class SimpleIntentRegistry:
    allowed_intents: Set[str] = field(default_factory=set)
    allowed_slots: Dict[str, Set[str]] = field(default_factory=dict)
    required_slots: Dict[str, Set[str]] = field(default_factory=dict)
    validators: Dict[str, SlotValidator] = field(default_factory=dict)

    def is_allowed(self, intent: str) -> bool:
        return intent in self.allowed_intents

    def validate_slots(self, intent: str, slots: Dict[str, object]) -> bool:
        if intent not in self.allowed_intents:
            return False
        allowed = self.allowed_slots.get(intent)
        if allowed is not None:
            if not set(slots).issubset(allowed):
                return False
        required = self.required_slots.get(intent)
        if required is not None:
            if not required.issubset(set(slots)):
                return False
        validator: Optional[SlotValidator] = self.validators.get(intent)
        if validator is not None and not validator(slots):
            return False
        return True
