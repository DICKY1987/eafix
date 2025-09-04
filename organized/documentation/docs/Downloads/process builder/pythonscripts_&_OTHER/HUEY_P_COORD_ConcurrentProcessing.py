#!/usr/bin/env python3
"""
Concurrent Processing Coordinator

Manages concurrent documentation processing tasks with proper coordination,
dependency resolution, and resource management.
"""

import asyncio
import logging
import threading
import time
import uuid
from concurrent.futures import Future, ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, IntEnum
from queue import PriorityQueue
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class TaskPriority(IntEnum):
    """
    Enumeration for task priority levels.

    Lower integer values represent higher priority.
    """

    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4
    BACKGROUND = 5


class TaskStatus(Enum):
    """Enumeration for the lifecycle status of a task."""

    PENDING = "pending"
    WAITING = "waiting"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceType(Enum):
    """Enumeration for types of system resources that can be locked."""

    FILE = "file"
    SECTION = "section"
    ARTIFACT_TYPE = "artifact_type"
    CACHE = "cache"
    DATABASE = "database"


@dataclass
class ProcessingTask:
    """
    Represents a documentation processing task.

    Attributes:
        task_id: Unique identifier for the task.
        name: A human-readable name for the task.
        function: The callable function that performs the task's work.
        args: Positional arguments to pass to the function.
        kwargs: Keyword arguments to pass to the function.
        priority: The priority of the task.
        dependencies: A set of task IDs that must be completed first.
        required_resources: A set of resources that must be locked.
        timeout_seconds: Optional timeout for task execution.
        retry_count: The current number of retry attempts.
        max_retries: The maximum number of times to retry a failed task.
        status: The current status of the task.
        created_at: Timestamp when the task was created.
        started_at: Timestamp when the task started execution.
        completed_at: Timestamp when the task finished execution.
        result: The return value of the function if it completed successfully.
        error: The exception object if the task failed.
        worker_id: The ID of the worker that executed the task.
    """

    task_id: str
    name: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: Set[str] = field(default_factory=set)
    required_resources: Set[Tuple[ResourceType, str]] = field(default_factory=set)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    worker_id: Optional[str] = None


@dataclass
class ResourceLock:
    """
    Represents a lock on a system resource.

    Attributes:
        resource_type: The type of the locked resource.
        resource_id: The unique ID of the locked resource.
        task_id: The ID of the task holding the lock.
        worker_id: The ID of the worker holding the lock.
        acquired_at: Timestamp when the lock was acquired.
        expires_at: Optional timestamp when the lock expires.
    """

    resource_type: ResourceType
    resource_id: str
    task_id: str
    worker_id: str
    acquired_at: datetime
    expires_at: Optional[datetime] = None


class DependencyGraph:
    """Manages task dependencies and resolves execution order."""

    def __init__(self):
        """Initializes the DependencyGraph."""
        self.dependencies: Dict[str, Set[str]] = {}
        self.dependents: Dict[str, Set[str]] = {}

    def add_dependency(self, task_id: str, depends_on: str):
        """
        Adds a dependency relationship between two tasks.

        Args:
            task_id: The ID of the task that has a dependency.
            depends_on: The ID of the task that must be completed first.
        """
        self.dependencies.setdefault(task_id, set()).add(depends_on)
        self.dependents.setdefault(depends_on, set()).add(task_id)

    def get_ready_tasks(self, all_tasks: Dict[str, ProcessingTask]) -> Set[str]:
        """
        Gets the set of tasks whose dependencies have been met.

        Args:
            all_tasks: A dictionary of all known tasks.

        Returns:
            A set of task IDs that are ready to be executed.
        """
        ready = set()
        for task_id, task in all_tasks.items():
            if task.status != TaskStatus.PENDING:
                continue
            
            deps = self.dependencies.get(task_id, set())
            if all(all_tasks.get(dep_id, {}).status == TaskStatus.COMPLETED for dep_id in deps):
                ready.add(task_id)
        return ready


class ResourceManager:
    """Manages resource locking for concurrent access."""

    def __init__(self):
        """Initializes the ResourceManager."""
        self.locks: Dict[Tuple[ResourceType, str], ResourceLock] = {}
        self.lock_mutex = threading.RLock()

    def acquire_resources(
        self, task_id: str, worker_id: str, resources: Set[Tuple[ResourceType, str]]
    ) -> bool:
        """
        Acquires locks on a set of resources for a task.

        Args:
            task_id: The ID of the task requesting the locks.
            worker_id: The ID of the worker requesting the locks.
            resources: A set of resource tuples to lock.

        Returns:
            True if all resources were successfully locked, False otherwise.
        """
        with self.lock_mutex:
            if any(res in self.locks for res in resources):
                return False  # At least one resource is already locked

            for resource in resources:
                lock = ResourceLock(
                    resource_type=resource[0],
                    resource_id=resource[1],
                    task_id=task_id,
                    worker_id=worker_id,
                    acquired_at=datetime.now(),
                )
                self.locks[resource] = lock
            return True

    def release_resources(self, task_id: str):
        """
        Releases all resource locks held by a specific task.

        Args:
            task_id: The ID of the task whose resources should be released.
        """
        with self.lock_mutex:
            to_remove = [res for res, lock in self.locks.items() if lock.task_id == task_id]
            for resource in to_remove:
                del self.locks[resource]


class ConcurrentDocumentationCoordinator:
    """Main coordinator for concurrent documentation processing."""

    def __init__(self, max_thread_workers: int = 4, max_process_workers: int = 2):
        """
        Initializes the coordinator.

        Args:
            max_thread_workers: Max number of threads for I/O-bound tasks.
            max_process_workers: Max number of processes for CPU-bound tasks.
        """
        self.tasks: Dict[str, ProcessingTask] = {}
        self.task_queue = PriorityQueue()
        self.dependency_graph = DependencyGraph()
        self.resource_manager = ResourceManager()
        self.thread_executor = ThreadPoolExecutor(max_workers=max_thread_workers)
        self.process_executor = ProcessPoolExecutor(max_workers=max_process_workers)
        self.active_futures: Dict[str, Future] = {}
        self.is_running = False
        self.coordinator_thread: Optional[threading.Thread] = None
        self.shutdown_event = threading.Event()

    def start(self):
        """Starts the coordinator's main processing loop."""
        if self.is_running:
            return
        self.is_running = True
        self.shutdown_event.clear()
        self.coordinator_thread = threading.Thread(
            target=self._coordinator_loop, name="DocCoordinator", daemon=True
        )
        self.coordinator_thread.start()
        logger.info("Documentation coordinator started.")

    def stop(self, timeout: int = 30):
        """
        Stops the coordinator and shuts down its executors.

        Args:
            timeout: The number of seconds to wait for graceful shutdown.
        """
        if not self.is_running:
            return
        logger.info("Stopping documentation coordinator...")
        self.shutdown_event.set()
        if self.coordinator_thread:
            self.coordinator_thread.join(timeout=timeout)
        self.thread_executor.shutdown(wait=True, cancel_futures=True)
        self.process_executor.shutdown(wait=True, cancel_futures=True)
        self.is_running = False
        logger.info("Documentation coordinator stopped.")

    def submit_task(self, task: ProcessingTask) -> str:
        """
        Submits a task for processing.

        Args:
            task: The ProcessingTask object to be executed.

        Returns:
            The ID of the submitted task.
        """
        self.tasks[task.task_id] = task
        for dep_id in task.dependencies:
            self.dependency_graph.add_dependency(task.task_id, dep_id)
        
        priority_tuple = (task.priority.value, task.created_at.timestamp(), task.task_id)
        self.task_queue.put(priority_tuple)
        logger.debug(f"Task {task.task_id} submitted with priority {task.priority.name}")
        return task.task_id

    def _coordinator_loop(self):
        """The main processing loop for the coordinator."""
        while not self.shutdown_event.is_set():
            try:
                self._check_completed_futures()
                self._process_ready_tasks()
                time.sleep(0.1)
            except Exception as e:
                logger.critical(f"Coordinator loop crashed: {e}", exc_info=True)
                self.is_running = False # Stop loop on critical error

    def _check_completed_futures(self):
        """Checks for completed tasks and updates their status."""
        completed_tasks = []
        for task_id, future in self.active_futures.items():
            if future.done():
                completed_tasks.append(task_id)
                task = self.tasks[task_id]
                try:
                    if future.cancelled():
                        task.status = TaskStatus.CANCELLED
                    else:
                        task.result = future.result()
                        task.status = TaskStatus.COMPLETED
                except Exception as e:
                    task.status = TaskStatus.FAILED
                    task.error = e
                    logger.error(f"Task {task_id} failed: {e}")
                
                task.completed_at = datetime.now()
                self.resource_manager.release_resources(task_id)

        for task_id in completed_tasks:
            del self.active_futures[task_id]

    def _process_ready_tasks(self):
        """Identifies and starts tasks that are ready for execution."""
        ready_task_ids = self.dependency_graph.get_ready_tasks(self.tasks)
        for task_id in ready_task_ids:
            task = self.tasks[task_id]
            if task.status != TaskStatus.PENDING:
                continue

            worker_id = f"worker_{uuid.uuid4().hex[:8]}"
            if self.resource_manager.acquire_resources(
                task_id, worker_id, task.required_resources
            ):
                self._start_task_execution(task, worker_id)
            else:
                task.status = TaskStatus.WAITING

    def _start_task_execution(self, task: ProcessingTask, worker_id: str):
        """Submits a task to the appropriate executor."""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        task.worker_id = worker_id

        executor = (
            self.process_executor
            if getattr(task.function, "_use_process_pool", False)
            else self.thread_executor
        )
        future = executor.submit(task.function, *task.args, **task.kwargs)
        self.active_futures[task.task_id] = future
        logger.debug(f"Task {task.task_id} started on worker {worker_id}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Concurrent Processing Coordinator is a framework and not meant to be run directly.")