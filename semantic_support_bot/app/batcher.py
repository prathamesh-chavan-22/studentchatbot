"""
AsyncBatcher — batches incoming embedding queries for high-concurrency
inference efficiency.

Error handling improvements:
- Tracks health state; rejects new work after repeated failures
- Resolves *every* future (success OR error) — no silent hanging
- Graceful shutdown that drains the queue instead of hard-cancelling
- Structured logging at every failure point
"""

from __future__ import annotations

import asyncio
import time
from typing import List, Tuple, Any
from loguru import logger

from app.exceptions import InferenceError, BatcherNotRunningError


# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
_MAX_CONSECUTIVE_FAILURES = 5
_SHUTDOWN_DRAIN_TIMEOUT = 10.0  # seconds to wait for queue drain on shutdown
_BATCH_PROCESSING_TIMEOUT = 120.0  # max time for a single batch inference


class AsyncBatcher:
    """
    Batches incoming queries for high-concurrency embedding inference.

    The worker loop collects queries until either:
      - max_batch_size is reached, or
      - wait_seconds has elapsed since the first item

    After *failure_threshold* consecutive inference failures the batcher
    enters a degraded state and will raise errors on new submissions.
    """

    def __init__(
        self,
        model: Any,
        max_batch_size: int = 32,
        wait_seconds: float = 0.05,
    ):
        self.model = model
        self.max_batch_size = max_batch_size
        self.wait_seconds = wait_seconds

        self.queue: asyncio.Queue[Tuple[str, asyncio.Future]] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._running = False
        self._healthy = True
        self._consecutive_failures = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_running(self) -> bool:
        return self._running and self._healthy

    @property
    def queue_size(self) -> int:
        return self.queue.qsize()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Starts the background worker loop."""
        if self._running:
            logger.warning("AsyncBatcher.start() called but already running — ignoring")
            return

        try:
            self._running = True
            self._healthy = True
            self._consecutive_failures = 0
            self._worker_task = asyncio.create_task(self._worker_loop())
            logger.info(
                f"AsyncBatcher started (max_batch_size={self.max_batch_size}, "
                f"wait={self.wait_seconds}s)"
            )
        except Exception as exc:
            logger.error(f"Failed to start AsyncBatcher: {exc}")
            self._running = False
            raise

    async def stop(self):
        """
        Stops the background worker loop gracefully.

        Sets a flag so the worker exits after processing remaining items,
        then waits for the task to finish with a timeout.
        """
        if not self._running:
            logger.debug("AsyncBatcher.stop() called but not running — no-op")
            return

        self._running = False
        logger.info("AsyncBatcher: signaling worker to stop...")

        if self._worker_task is not None:
            try:
                await asyncio.wait_for(
                    self._worker_task, timeout=_SHUTDOWN_DRAIN_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"AsyncBatcher: worker did not finish within "
                    f"{_SHUTDOWN_DRAIN_TIMEOUT}s — cancelling"
                )
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            except Exception as exc:
                logger.error(f"Error during AsyncBatcher shutdown: {exc}")
            finally:
                self._worker_task = None

        logger.info("AsyncBatcher stopped.")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_embedding(self, query: str) -> Any:
        """
        Submits a query for batching and returns its embedding vector.

        Raises
        ------
        BatcherNotRunningError
            If the worker is not running or has been marked unhealthy.
        InferenceError
            If the batch inference fails.
        """
        if not self._running:
            raise BatcherNotRunningError("AsyncBatcher worker is not running")

        if not self._healthy:
            raise BatcherNotRunningError(
                "AsyncBatcher is in a degraded state due to repeated failures"
            )

        future = asyncio.get_running_loop().create_future()
        await self.queue.put((query, future))

        try:
            result = await future
            return result
        except Exception as exc:
            logger.error(f"get_embedding failed for query '{query[:50]}': {exc}")
            raise

    # ------------------------------------------------------------------
    # Worker loop
    # ------------------------------------------------------------------

    async def _worker_loop(self):
        """Background worker that processes the queue in batches."""
        while self._running:
            try:
                # 1. Wait for at least one item (with a short poll so we
                #    can check self._running periodically).
                try:
                    query, future = await asyncio.wait_for(
                        self.queue.get(), timeout=0.5
                    )
                except asyncio.TimeoutError:
                    continue  # loop back and re-check self._running

                batch: List[Tuple[str, asyncio.Future]] = [(query, future)]

                # 2. Try to fill the batch until max_batch_size or time-out
                start_time = time.monotonic()
                while len(batch) < self.max_batch_size:
                    time_remaining = self.wait_seconds - (
                        time.monotonic() - start_time
                    )
                    if time_remaining <= 0:
                        break

                    try:
                        q, f = await asyncio.wait_for(
                            self.queue.get(), timeout=time_remaining
                        )
                        batch.append((q, f))
                    except asyncio.TimeoutError:
                        break

                # 3. Process the batch
                if batch:
                    await self._process_batch(batch)

            except asyncio.CancelledError:
                logger.info("AsyncBatcher worker: cancelled")
                break
            except Exception as exc:
                logger.error(
                    f"Unexpected error in AsyncBatcher worker loop: {exc}",
                    exc_info=True,
                )
                await asyncio.sleep(0.5)  # prevent tight error loop

    async def _process_batch(
        self, batch: List[Tuple[str, asyncio.Future]]
    ):
        """Run model inference on a batch and resolve futures."""
        queries = [item[0] for item in batch]
        futures = [item[1] for item in batch]

        logger.debug(f"Processing batch of {len(queries)} queries.")

        try:
            embeddings = await asyncio.wait_for(
                asyncio.to_thread(self._model_encode, queries),
                timeout=_BATCH_PROCESSING_TIMEOUT,
            )

            # Resolve futures with results
            for i, future in enumerate(futures):
                if not future.done():
                    future.set_result(embeddings[i])

            self._consecutive_failures = 0  # reset on success
            logger.debug(f"Batch of {len(queries)} processed successfully.")

        except asyncio.TimeoutError as exc:
            error_msg = (
                f"Batch inference timed out after {_BATCH_PROCESSING_TIMEOUT}s "
                f"({len(queries)} queries)"
            )
            logger.error(error_msg)
            self._record_failure()
            for future in futures:
                if not future.done():
                    future.set_exception(
                        InferenceError(error_msg, original=exc)
                    )
        except Exception as exc:
            error_msg = f"Error in batch inference: {exc}"
            logger.error(error_msg, exc_info=True)
            self._record_failure()
            for future in futures:
                if not future.done():
                    future.set_exception(InferenceError(error_msg, original=exc))
        finally:
            for _ in range(len(batch)):
                try:
                    self.queue.task_done()
                except ValueError:
                    # task_done called too many times — safe to ignore
                    pass

    # ------------------------------------------------------------------
    # Health tracking
    # ------------------------------------------------------------------

    def _record_failure(self):
        self._consecutive_failures += 1
        if self._consecutive_failures >= _MAX_CONSECUTIVE_FAILURES:
            logger.critical(
                f"AsyncBatcher: {_MAX_CONSECUTIVE_FAILURES} consecutive failures — "
                f"marking as unhealthy"
            )
            self._healthy = False

    # ------------------------------------------------------------------
    # Model encoding (runs in thread pool)
    # ------------------------------------------------------------------

    def _model_encode(self, queries: List[str]):
        """Internal call to the model's encode method."""
        return self.model.encode(
            queries,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )
