"""Parallel Processing Framework - Unified parallel execution for pipeline.

This module provides a flexible parallel processing system that can be used
by all pipeline stages to process multiple files or tasks concurrently.
"""

import asyncio
import logging
import multiprocessing
import queue
import threading
import time
from concurrent.futures import (
    ProcessPoolExecutor,
    ThreadPoolExecutor,
    as_completed,
)
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ExecutorType(Enum):
    """Parallel executor types."""

    THREAD = "thread"
    PROCESS = "process"
    ASYNC = "async"
    SERIAL = "serial"  # For debugging


@dataclass
class TaskResult:
    """Result from a parallel task."""

    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class BatchResult:
    """Result from batch processing."""

    total_tasks: int
    successful: int
    failed: int
    results: List[TaskResult]
    total_duration: float

    @property
    def success_rate(self) -> float:
        """Get success rate.

        Returns:
            Success rate (0-1)
        """
        if self.total_tasks == 0:
            return 0.0
        return self.successful / self.total_tasks


class WorkQueue:
    """Thread-safe work queue."""

    def __init__(self, maxsize: int = 0):
        """Initialize work queue.

        Args:
            maxsize: Maximum queue size (0 for unlimited)
        """
        self.queue = queue.Queue(maxsize=maxsize)
        self.processed = 0
        self.lock = threading.Lock()

    def put(self, item: Any) -> None:
        """Add item to queue.

        Args:
            item: Work item
        """
        self.queue.put(item)

    def get(self, timeout: Optional[float] = None) -> Any:
        """Get item from queue.

        Args:
            timeout: Timeout in seconds

        Returns:
            Work item
        """
        item = self.queue.get(timeout=timeout)

        with self.lock:
            self.processed += 1

        return item

    def done(self) -> None:
        """Mark task as done."""
        self.queue.task_done()

    def join(self) -> None:
        """Wait for all tasks to complete."""
        self.queue.join()

    @property
    def size(self) -> int:
        """Get queue size.

        Returns:
            Number of items in queue
        """
        return self.queue.qsize()

    @property
    def empty(self) -> bool:
        """Check if queue is empty.

        Returns:
            True if empty
        """
        return self.queue.empty()


class ParallelExecutor:
    """Parallel task executor."""

    def __init__(
        self,
        executor_type: ExecutorType = ExecutorType.THREAD,
        max_workers: Optional[int] = None,
    ):
        """Initialize parallel executor.

        Args:
            executor_type: Type of executor to use
            max_workers: Maximum number of workers
        """
        self.executor_type = executor_type
        self.max_workers = max_workers or self._get_default_workers()

    def execute(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable[[TaskResult], None]] = None,
    ) -> BatchResult:
        """Execute function on items in parallel.

        Args:
            func: Function to execute
            items: Items to process
            callback: Optional callback for each result

        Returns:
            Batch processing result
        """
        if self.executor_type == ExecutorType.SERIAL:
            return self._execute_serial(func, items, callback)
        elif self.executor_type == ExecutorType.THREAD:
            return self._execute_threaded(func, items, callback)
        elif self.executor_type == ExecutorType.PROCESS:
            return self._execute_multiprocess(func, items, callback)
        elif self.executor_type == ExecutorType.ASYNC:
            return self._execute_async(func, items, callback)
        else:
            raise ValueError(f"Unknown executor type: {self.executor_type}")

    def map(
        self,
        func: Callable,
        items: List[Any],
        chunksize: int = 1,
    ) -> Iterator[Any]:
        """Map function over items in parallel.

        Args:
            func: Function to map
            items: Items to process
            chunksize: Chunk size for processing

        Yields:
            Results from function
        """
        if self.executor_type == ExecutorType.SERIAL:
            for item in items:
                yield func(item)

        elif self.executor_type == ExecutorType.THREAD:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                for result in executor.map(func, items, chunksize=chunksize):
                    yield result

        elif self.executor_type == ExecutorType.PROCESS:
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                for result in executor.map(func, items, chunksize=chunksize):
                    yield result

        else:
            # Async requires different handling
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:

                async def async_map():
                    tasks = [self._to_async(func, item) for item in items]
                    results = await asyncio.gather(*tasks)
                    return results

                results = loop.run_until_complete(async_map())
                for result in results:
                    yield result

            finally:
                loop.close()

    def _execute_serial(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable],
    ) -> BatchResult:
        """Execute serially (for debugging).

        Args:
            func: Function to execute
            items: Items to process
            callback: Optional callback

        Returns:
            Batch result
        """
        start_time = time.time()
        results = []
        successful = 0
        failed = 0

        for i, item in enumerate(items):
            task_start = time.time()
            task_id = f"task_{i}"

            try:
                result = func(item)
                task_result = TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                    duration=time.time() - task_start,
                )
                successful += 1

            except Exception as e:
                task_result = TaskResult(
                    task_id=task_id,
                    success=False,
                    result=None,
                    error=str(e),
                    duration=time.time() - task_start,
                )
                failed += 1

            results.append(task_result)

            if callback:
                callback(task_result)

        return BatchResult(
            total_tasks=len(items),
            successful=successful,
            failed=failed,
            results=results,
            total_duration=time.time() - start_time,
        )

    def _execute_threaded(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable],
    ) -> BatchResult:
        """Execute with threads.

        Args:
            func: Function to execute
            items: Items to process
            callback: Optional callback

        Returns:
            Batch result
        """
        start_time = time.time()
        results = []
        successful = 0
        failed = 0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for i, item in enumerate(items):
                task_id = f"task_{i}"
                future = executor.submit(func, item)
                futures[future] = (task_id, item, time.time())

            # Collect results
            for future in as_completed(futures):
                task_id, item, task_start = futures[future]

                try:
                    result = future.result()
                    task_result = TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration=time.time() - task_start,
                    )
                    successful += 1

                except Exception as e:
                    task_result = TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        error=str(e),
                        duration=time.time() - task_start,
                    )
                    failed += 1

                results.append(task_result)

                if callback:
                    callback(task_result)

        return BatchResult(
            total_tasks=len(items),
            successful=successful,
            failed=failed,
            results=results,
            total_duration=time.time() - start_time,
        )

    def _execute_multiprocess(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable],
    ) -> BatchResult:
        """Execute with processes.

        Args:
            func: Function to execute
            items: Items to process
            callback: Optional callback

        Returns:
            Batch result
        """
        start_time = time.time()
        results = []
        successful = 0
        failed = 0

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for i, item in enumerate(items):
                task_id = f"task_{i}"
                future = executor.submit(func, item)
                futures[future] = (task_id, item, time.time())

            # Collect results
            for future in as_completed(futures):
                task_id, item, task_start = futures[future]

                try:
                    result = future.result()
                    task_result = TaskResult(
                        task_id=task_id,
                        success=True,
                        result=result,
                        duration=time.time() - task_start,
                    )
                    successful += 1

                except Exception as e:
                    task_result = TaskResult(
                        task_id=task_id,
                        success=False,
                        result=None,
                        error=str(e),
                        duration=time.time() - task_start,
                    )
                    failed += 1

                results.append(task_result)

                if callback:
                    callback(task_result)

        return BatchResult(
            total_tasks=len(items),
            successful=successful,
            failed=failed,
            results=results,
            total_duration=time.time() - start_time,
        )

    def _execute_async(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable],
    ) -> BatchResult:
        """Execute asynchronously.

        Args:
            func: Function to execute
            items: Items to process
            callback: Optional callback

        Returns:
            Batch result
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(self._async_execute(func, items, callback))
        finally:
            loop.close()

    async def _async_execute(
        self,
        func: Callable,
        items: List[Any],
        callback: Optional[Callable],
    ) -> BatchResult:
        """Async execution helper.

        Args:
            func: Function to execute
            items: Items to process
            callback: Optional callback

        Returns:
            Batch result
        """
        start_time = time.time()
        results = []
        successful = 0
        failed = 0

        # Create tasks
        tasks = []
        for i, item in enumerate(items):
            task_id = f"task_{i}"
            task = self._async_task(func, item, task_id)
            tasks.append(task)

        # Execute and collect
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(task_results):
            task_id = f"task_{i}"

            if isinstance(result, Exception):
                task_result = TaskResult(
                    task_id=task_id,
                    success=False,
                    result=None,
                    error=str(result),
                )
                failed += 1
            else:
                task_result = TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                )
                successful += 1

            results.append(task_result)

            if callback:
                callback(task_result)

        return BatchResult(
            total_tasks=len(items),
            successful=successful,
            failed=failed,
            results=results,
            total_duration=time.time() - start_time,
        )

    async def _async_task(self, func: Callable, item: Any, task_id: str) -> Any:
        """Execute async task.

        Args:
            func: Function to execute
            item: Item to process
            task_id: Task identifier

        Returns:
            Task result
        """
        if asyncio.iscoroutinefunction(func):
            return await func(item)
        else:
            # Run sync function in thread
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, item)

    async def _to_async(self, func: Callable, item: Any) -> Any:
        """Convert sync function to async.

        Args:
            func: Function to convert
            item: Item to process

        Returns:
            Result
        """
        if asyncio.iscoroutinefunction(func):
            return await func(item)
        else:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, item)

    def _get_default_workers(self) -> int:
        """Get default number of workers.

        Returns:
            Default worker count
        """
        if self.executor_type == ExecutorType.PROCESS:
            return min(4, multiprocessing.cpu_count())
        elif self.executor_type == ExecutorType.THREAD:
            return min(8, multiprocessing.cpu_count() * 2)
        else:
            return 1


class Pipeline:
    """Parallel pipeline for chaining operations."""

    def __init__(self, executor: Optional[ParallelExecutor] = None):
        """Initialize pipeline.

        Args:
            executor: Parallel executor to use
        """
        self.executor = executor or ParallelExecutor()
        self.stages: List[Tuple[str, Callable]] = []

    def add_stage(self, name: str, func: Callable) -> "Pipeline":
        """Add processing stage.

        Args:
            name: Stage name
            func: Processing function

        Returns:
            Self for chaining
        """
        self.stages.append((name, func))
        return self

    def process(self, items: List[Any]) -> Dict[str, BatchResult]:
        """Process items through pipeline.

        Args:
            items: Items to process

        Returns:
            Results from each stage
        """
        results = {}
        current_items = items

        for stage_name, stage_func in self.stages:
            logger.info(f"Running pipeline stage: {stage_name}")

            # Execute stage
            batch_result = self.executor.execute(stage_func, current_items)
            results[stage_name] = batch_result

            # Collect successful results for next stage
            current_items = [
                r.result
                for r in batch_result.results
                if r.success and r.result is not None
            ]

            if not current_items:
                logger.warning(f"No items to process after stage {stage_name}")
                break

        return results


def parallel_map(
    func: Callable,
    items: List[Any],
    executor_type: ExecutorType = ExecutorType.THREAD,
    max_workers: Optional[int] = None,
) -> List[Any]:
    """Convenience function for parallel map.

    Args:
        func: Function to map
        items: Items to process
        executor_type: Type of executor
        max_workers: Maximum workers

    Returns:
        Mapped results
    """
    executor = ParallelExecutor(executor_type, max_workers)
    return list(executor.map(func, items))


def parallel_execute(
    func: Callable,
    items: List[Any],
    executor_type: ExecutorType = ExecutorType.THREAD,
    max_workers: Optional[int] = None,
) -> BatchResult:
    """Convenience function for parallel execution.

    Args:
        func: Function to execute
        items: Items to process
        executor_type: Type of executor
        max_workers: Maximum workers

    Returns:
        Batch result
    """
    executor = ParallelExecutor(executor_type, max_workers)
    return executor.execute(func, items)
