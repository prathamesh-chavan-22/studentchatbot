"""
Retry utility with exponential backoff and jitter.

Use this for transient failures (network blips, temporary resource
unavailability) — NEVER for permanent errors like bad input.
"""

from __future__ import annotations

import asyncio
import random
import time
from typing import Callable, Any, Type, Tuple
from loguru import logger


DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0
DEFAULT_MAX_DELAY = 30.0
DEFAULT_JITTER_RANGE = (0, 1000)  # milliseconds


def _calculate_delay(
    attempt: int,
    base_delay: float,
    max_delay: float,
    jitter_range: Tuple[float, float],
) -> float:
    """Exponential backoff with random jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(*jitter_range) / 1000.0  # convert ms -> seconds
    return delay + jitter


async def retry_async(
    fn: Callable,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter_range: Tuple[float, float] = DEFAULT_JITTER_RANGE,
    retryable_exceptions: Tuple[Type[Exception], ...] | None = None,
    operation_name: str = "operation",
) -> Any:
    """
    Retry an async function with exponential backoff + jitter.

    Only retries if the raised exception is in *retryable_exceptions*.
    All other exceptions propagate immediately (permanent errors).

    Parameters
    ----------
    fn : Callable
        The async (or sync) function to call.
    max_retries : int
        Maximum number of *additional* attempts (total = max_retries + 1).
    base_delay : float
        Base delay in seconds; actual delay = base * 2^attempt + jitter.
    max_delay : float
        Upper bound on the delay.
    jitter_range : tuple
        Random jitter range in milliseconds.
    retryable_exceptions : tuple[Exception, ...]
        Only these exception types trigger a retry. If None, retries all exceptions.
    operation_name : str
        Human-readable name used in log messages.

    Returns
    -------
    The return value of *fn*.

    Raises
    ------
    The last exception raised if all retries are exhausted.
    """
    exceptions_to_catch = retryable_exceptions or (Exception,)
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            if asyncio.iscoroutinefunction(fn):
                return await fn()
            else:
                return fn()
        except exceptions_to_catch as exc:
            last_exc = exc
            if attempt == max_retries:
                logger.error(
                    f"{operation_name}: all {max_retries + 1} attempts exhausted. "
                    f"Last error: {exc}"
                )
                raise

            delay = _calculate_delay(attempt, base_delay, max_delay, jitter_range)
            logger.warning(
                f"{operation_name}: attempt {attempt + 1}/{max_retries + 1} failed "
                f"({exc.__class__.__name__}: {exc}). Retrying in {delay:.2f}s..."
            )
            await asyncio.sleep(delay)
        except BaseException:
            # Never retry KeyboardInterrupt, SystemExit, etc.
            raise

    # Should never reach here, but satisfy type checkers
    raise last_exc  # type: ignore[misc]


def retry_sync(
    fn: Callable,
    *,
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
    jitter_range: Tuple[float, float] = DEFAULT_JITTER_RANGE,
    retryable_exceptions: Tuple[Type[Exception], ...] | None = None,
    operation_name: str = "operation",
) -> Any:
    """
    Synchronous variant of retry_async.
    """
    exceptions_to_catch = retryable_exceptions or (Exception,)
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return fn()
        except exceptions_to_catch as exc:
            last_exc = exc
            if attempt == max_retries:
                logger.error(
                    f"{operation_name}: all {max_retries + 1} attempts exhausted. "
                    f"Last error: {exc}"
                )
                raise

            delay = _calculate_delay(attempt, base_delay, max_delay, jitter_range)
            logger.warning(
                f"{operation_name}: attempt {attempt + 1}/{max_retries + 1} failed "
                f"({exc.__class__.__name__}: {exc}). Retrying in {delay:.2f}s..."
            )
            time.sleep(delay)
        except BaseException:
            raise

    raise last_exc  # type: ignore[misc]
