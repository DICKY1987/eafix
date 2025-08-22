#!/usr/bin/env python3
"""
Documentation State Management Engine

Provides robust state management, recovery, and coordination for documentation
processing. This module solves core data architecture gaps by providing a
persistent, transactional state layer for the documentation system.
"""

import hashlib
import json
import logging
import sqlite3
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

logger = logging.getLogger(__name__)


class ProcessingState(Enum):
    """Enumeration for the state of a processing job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ProcessingJob:
    """
    Represents a single documentation processing job.

    Attributes:
        job_id: A unique identifier for the job.
        file_path: The path to the file being processed.
        content_hash: The SHA-256 hash of the file content at job creation.
        state: The current state of the job.
        progress: The completion percentage (0.0 to 100.0).
        started_at: Timestamp when processing started.
        completed_at: Timestamp when processing finished.
        error_message: An error message if the job failed.
        checkpoints: A dictionary to store intermediate results or state.
    """

    job_id: str
    file_path: str
    content_hash: str
    state: ProcessingState
    progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    checkpoints: Dict[str, Any] = field(default_factory=dict)


class DocumentationStateManager:
    """
    Core state management for documentation processing.

    This class handles the persistent storage and retrieval of job states,
    processing locks, and cached results using an SQLite database.
    """

    def __init__(self, db_path: str = "documentation_state.db"):
        """
        Initializes the state manager.

        Args:
            db_path: The path to the SQLite database file.
        """
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Creates the database schema if it doesn't exist."""
        try:
            with self._connect() as conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processing_jobs (
                        job_id TEXT PRIMARY KEY, file_path TEXT NOT NULL,
                        content_hash TEXT NOT NULL, state TEXT NOT NULL,
                        progress REAL DEFAULT 0.0, started_at TEXT, completed_at TEXT,
                        error_message TEXT, checkpoints TEXT, created_at TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS processing_locks (
                        resource_id TEXT PRIMARY KEY, job_id TEXT NOT NULL,
                        locked_at TEXT NOT NULL, expires_at TEXT NOT NULL
                    )
                    """
                )
        except sqlite3.Error as e:
            logger.critical(f"Database initialization failed: {e}")
            raise

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Provides a transactional database connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        try:
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            conn.close()

    def create_job(self, file_path: str) -> Optional[str]:
        """
        Creates a new processing job for a given file.

        Args:
            file_path: The path to the file to be processed.

        Returns:
            The job ID if created successfully, otherwise None.
        """
        try:
            content = Path(file_path).read_text(encoding="utf-8")
            content_hash = hashlib.sha256(content.encode()).hexdigest()
        except (IOError, OSError) as e:
            logger.error(f"Could not read file for job creation: {e}")
            return None

        job_id = f"job_{int(time.time() * 1000)}_{content_hash[:8]}"
        job = ProcessingJob(
            job_id=job_id, file_path=file_path, content_hash=content_hash,
            state=ProcessingState.PENDING
        )

        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO processing_jobs (job_id, file_path, content_hash, state, checkpoints, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (job_id, file_path, content_hash, job.state.value, "{}", datetime.now().isoformat()),
                )
            return job_id
        except sqlite3.Error as e:
            logger.error(f"Failed to create job in database: {e}")
            return None

    def update_job_state(
        self, job_id: str, state: ProcessingState, progress: Optional[float] = None
    ):
        """
        Updates the state and progress of a job.

        Args:
            job_id: The ID of the job to update.
            state: The new state of the job.
            progress: The new progress percentage (optional).
        """
        updates = {"state": state.value}
        if progress is not None:
            updates["progress"] = progress
        if state == ProcessingState.PROCESSING:
            updates["started_at"] = datetime.now().isoformat()
        elif state in [ProcessingState.COMPLETED, ProcessingState.FAILED]:
            updates["completed_at"] = datetime.now().isoformat()
        
        set_clause = ", ".join([f"{key} = ?" for key in updates])
        values = list(updates.values()) + [job_id]

        try:
            with self._connect() as conn:
                conn.execute(f"UPDATE processing_jobs SET {set_clause} WHERE job_id = ?", values)
        except sqlite3.Error as e:
            logger.error(f"Failed to update job {job_id}: {e}")

    @contextmanager
    def acquire_lock(self, resource_id: str, job_id: str, timeout_seconds: int = 300):
        """
        Acquires a processing lock on a resource.

        Args:
            resource_id: The unique ID of the resource to lock.
            job_id: The ID of the job acquiring the lock.
            timeout_seconds: The duration for which the lock is valid.

        Yields:
            True if the lock was acquired.

        Raises:
            RuntimeError: If the resource is already locked by another job.
        """
        expires_at = datetime.now() + timedelta(seconds=timeout_seconds)
        lock_acquired = False
        try:
            with self._connect() as conn:
                try:
                    conn.execute(
                        "INSERT INTO processing_locks (resource_id, job_id, locked_at, expires_at) VALUES (?, ?, ?, ?)",
                        (resource_id, job_id, datetime.now().isoformat(), expires_at.isoformat()),
                    )
                    lock_acquired = True
                except sqlite3.IntegrityError:
                    # Check if the existing lock is expired
                    cursor = conn.execute("SELECT expires_at FROM processing_locks WHERE resource_id = ?", (resource_id,))
                    row = cursor.fetchone()
                    if row and datetime.fromisoformat(row[0]) < datetime.now():
                        conn.execute("DELETE FROM processing_locks WHERE resource_id = ?", (resource_id,))
                        # Retry insertion
                        conn.execute(
                            "INSERT INTO processing_locks (resource_id, job_id, locked_at, expires_at) VALUES (?, ?, ?, ?)",
                            (resource_id, job_id, datetime.now().isoformat(), expires_at.isoformat()),
                        )
                        lock_acquired = True
                    else:
                        raise RuntimeError(f"Resource '{resource_id}' is currently locked.")
            yield lock_acquired
        finally:
            if lock_acquired:
                with self._connect() as conn:
                    conn.execute("DELETE FROM processing_locks WHERE resource_id = ? AND job_id = ?", (resource_id, job_id))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    state_manager = DocumentationStateManager(db_path="test_doc_state.db")
    job_id = state_manager.create_job(__file__)
    if job_id:
        logger.info(f"Created job with ID: {job_id}")
        try:
            with state_manager.acquire_lock(__file__, job_id) as acquired:
                if acquired:
                    logger.info("Lock acquired successfully.")
                    state_manager.update_job_state(job_id, ProcessingState.PROCESSING, 50.0)
                    logger.info("Job state updated.")
            logger.info("Lock released.")
        except RuntimeError as e:
            logger.error(e)