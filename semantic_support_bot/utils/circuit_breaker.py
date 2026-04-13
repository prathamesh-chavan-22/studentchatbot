"""
Circuit breaker implementation for protecting external dependencies
(model inference, FAISS operations, file I/O).

States:
  CLOSED   — normal operation, requests pass through
  OPEN     — failure threshold exceeded, requests fail fast
  HALF_OPEN — testing recovery with a single probe request
"""

from __future__ import annotations

import asyncio
import time
import functools
from enum import Enum
from typing import Callable, Any
from loguru import logger


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    """Raised when a call is rejected because the circuit is OPEN."""
    pass


class CircuitBreaker:
    """
    A circuit breaker that trips after *failure_threshold* failures within
    *recovery_timeout* seconds.

    Usage:
        cb = CircuitBreaker(name="model_inference", failure_threshold=5, recovery_timeout=60)

        # Wrap a sync or async callable:
        result = await cb.call(async_fn, *args, **kwargs)
    """

    def __init__(
        self,
        *,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float = 0.0
        self._success_count = 0

    # -- Public properties --------------------------------------------------

    @property
    def state(self) -> CircuitState:
        """Check state and auto-transition from OPEN -> HALF_OPEN if timeout elapsed."""
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                logger.info(
                    f"CircuitBreaker '{self.name}': transitioning OPEN -> HALF_OPEN "
                    f"(recovery timeout {self.recovery_timeout}s elapsed)"
                )
                self._state = CircuitState.HALF_OPEN
        return self._state

    @property
    def failure_count(self) -> int:
        return self._failure_count

    # -- Core call method ---------------------------------------------------

    async def call(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute *fn* through the circuit breaker."""
        current_state = self.state  # triggers auto-transition check

        if current_state == CircuitState.OPEN:
            logger.warning(
                f"CircuitBreaker '{self.name}': rejecting call (circuit OPEN, "
                f"{self._failure_count} failures)"
            )
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN — call rejected"
            )

        try:
            if asyncio.iscoroutinefunction(fn):
                result = await fn(*args, **kwargs)
            else:
                result = fn(*args, **kwargs)

            self._on_success()
            return result

        except CircuitBreakerError:
            raise  # don't count our own rejection as a failure
        except Exception as exc:
            self._on_failure()
            raise

    # -- State transitions --------------------------------------------------

    def _on_success(self):
        if self._state == CircuitState.HALF_OPEN:
            logger.info(
                f"CircuitBreaker '{self.name}': HALF_OPEN -> CLOSED "
                f"(probe request succeeded)"
            )
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 1
        else:
            self._failure_count = 0
            self._success_count += 1

    def _on_failure(self):
        self._failure_count += 1
        self._last_failure_time = time.monotonic()

        if self._state == CircuitState.HALF_OPEN:
            logger.warning(
                f"CircuitBreaker '{self.name}': HALF_OPEN -> OPEN "
                f"(probe request failed)"
            )
            self._state = CircuitState.OPEN
            return

        if self._failure_count >= self.failure_threshold:
            logger.warning(
                f"CircuitBreaker '{self.name}': CLOSED -> OPEN "
                f"(threshold {self.failure_threshold} reached)"
            )
            self._state = CircuitState.OPEN

    # -- Convenience --------------------------------------------------------

    def reset(self):
        """Manually reset the breaker to CLOSED state."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = 0.0
        logger.info(f"CircuitBreaker '{self.name}': manually reset to CLOSED")


def with_circuit_breaker(
    breaker: CircuitBreaker,
):
    """
    Decorator that wraps an async function with a circuit breaker.

    Usage:
        model_cb = CircuitBreaker(name="model_inference")

        @with_circuit_breaker(model_cb)
        async def run_inference(queries):
            return model.encode(queries)
    """
    def decorator(fn: Callable):
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs):
            return await breaker.call(fn, *args, **kwargs)
        return wrapper
    return decorator
