from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class CircuitBreakerState:
    failure_count: int = 0
    opened_at: float | None = None


class CircuitBreaker:
    def __init__(
        self,
        enabled: bool = True,
        failure_threshold: int = 3,
        recovery_seconds: float = 30,
        now: Callable[[], float] = time.monotonic,
    ) -> None:
        self._enabled = enabled
        self._failure_threshold = max(1, failure_threshold)
        self._recovery_seconds = max(0, recovery_seconds)
        self._now = now
        self._states: dict[str, CircuitBreakerState] = {}

    def can_call(self, instance_id: str) -> bool:
        if not self._enabled:
            return True

        state = self._states.get(instance_id)
        if state is None or state.opened_at is None:
            return True

        return self._now() - state.opened_at >= self._recovery_seconds

    def record_success(self, instance_id: str) -> None:
        if not self._enabled:
            return
        self._states.pop(instance_id, None)

    def record_failure(self, instance_id: str) -> None:
        if not self._enabled:
            return

        state = self._states.setdefault(instance_id, CircuitBreakerState())
        state.failure_count += 1
        if state.failure_count >= self._failure_threshold:
            state.opened_at = self._now()

    def snapshot(self) -> dict[str, dict[str, float | int | bool | None]]:
        return {
            instance_id: {
                "failureCount": state.failure_count,
                "openedAt": state.opened_at,
                "open": state.opened_at is not None and not self.can_call(instance_id),
            }
            for instance_id, state in self._states.items()
        }
