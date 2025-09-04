#!/usr/bin/env python3
"""
Documentation Recovery & Rollback System

Provides comprehensive recovery and rollback capabilities for the documentation
processing system. Ensures the system can return to a known-good, consistent
state after failures.
"""

import contextlib
import gzip
import hashlib
import json
import logging
import shutil
import sqlite3
import tarfile
import tempfile
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RecoveryPointType(Enum):
    """Enumeration for different types of recovery points."""

    AUTOMATIC = "automatic"
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    PRE_OPERATION = "pre_operation"


class RecoveryStatus(Enum):
    """Enumeration for the status of a recovery point."""

    VALID = "valid"
    CORRUPTED = "corrupted"
    EXPIRED = "expired"
    RESTORED = "restored"


@dataclass
class RecoveryPoint:
    """
    Represents a point-in-time recovery snapshot.

    Attributes:
        recovery_id: A unique identifier for the recovery point.
        name: A human-readable name for the recovery point.
        description: A brief description of the snapshot's purpose.
        recovery_type: The type of recovery point.
        created_at: The timestamp when the snapshot was created.
        expires_at: Optional timestamp when the snapshot should be deleted.
        file_checksums: A dictionary mapping file paths to their SHA-256 checksums.
        backup_path: The path to the compressed backup archive.
        compressed_size_bytes: The size of the backup archive in bytes.
        status: The current status of the recovery point.
        metadata: A dictionary for storing additional metadata.
    """

    recovery_id: str
    name: str
    description: str
    recovery_type: RecoveryPointType
    created_at: datetime
    expires_at: Optional[datetime]
    file_checksums: Dict[str, str]
    backup_path: str
    compressed_size_bytes: int
    status: RecoveryStatus
    metadata: Dict[str, Any]


class DocumentationBackupManager:
    """
    Manages the creation, storage, and restoration of recovery points.
    """

    def __init__(self, backup_directory: str = "doc_backups", retention_days: int = 30):
        """
        Initializes the backup manager.

        Args:
            backup_directory: The directory to store backup files.
            retention_days: The default number of days to retain backups.
        """
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(exist_ok=True)
        self.retention_days = retention_days
        self.db_path = self.backup_directory / "recovery_tracking.db"
        self._initialize_database()

    def _initialize_database(self):
        """Initializes the SQLite database for tracking recovery points."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recovery_points (
                        recovery_id TEXT PRIMARY KEY, name TEXT NOT NULL,
                        description TEXT, recovery_type TEXT NOT NULL,
                        created_at TEXT NOT NULL, expires_at TEXT,
                        backup_path TEXT NOT NULL, compressed_size_bytes INTEGER,
                        status TEXT NOT NULL, metadata TEXT, file_checksums TEXT
                    )
                    """
                )
        except sqlite3.Error as e:
            logger.critical(f"Database initialization failed: {e}")
            raise

    def create_recovery_point(
        self,
        name: str,
        description: str,
        source_paths: List[str],
        recovery_type: RecoveryPointType = RecoveryPointType.MANUAL,
    ) -> Optional[str]:
        """
        Creates a new recovery point by archiving the source paths.

        Args:
            name: A name for the recovery point.
            description: A description of the recovery point.
            source_paths: A list of file or directory paths to include in the backup.
            recovery_type: The type of the recovery point.

        Returns:
            The ID of the created recovery point, or None on failure.
        """
        recovery_id = f"recovery_{int(datetime.now().timestamp() * 1000)}"
        backup_path = self.backup_directory / f"{recovery_id}.tar.gz"

        try:
            file_checksums = self._create_backup_archive(source_paths, backup_path)
            compressed_size = backup_path.stat().st_size
            expires_at = datetime.now() + timedelta(days=self.retention_days)

            recovery_point = RecoveryPoint(
                recovery_id=recovery_id, name=name, description=description,
                recovery_type=recovery_type, created_at=datetime.now(),
                expires_at=expires_at, file_checksums=file_checksums,
                backup_path=str(backup_path), compressed_size_bytes=compressed_size,
                status=RecoveryStatus.VALID, metadata={"source_paths": source_paths}
            )

            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    INSERT INTO recovery_points (recovery_id, name, description, recovery_type,
                    created_at, expires_at, backup_path, compressed_size_bytes, status,
                    metadata, file_checksums) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        recovery_id, name, description, recovery_type.value,
                        recovery_point.created_at.isoformat(),
                        recovery_point.expires_at.isoformat(), str(backup_path),
                        compressed_size, RecoveryStatus.VALID.value,
                        json.dumps(recovery_point.metadata),
                        json.dumps(file_checksums),
                    ),
                )
            logger.info(f"Created recovery point '{name}' ({recovery_id})")
            return recovery_id
        except (IOError, tarfile.TarError, sqlite3.Error) as e:
            logger.error(f"Failed to create recovery point '{name}': {e}")
            if backup_path.exists():
                backup_path.unlink()
            return None

    def _create_backup_archive(self, source_paths: List[str], backup_path: Path) -> Dict[str, str]:
        """Creates a compressed tar archive from source paths."""
        file_checksums = {}
        with tarfile.open(backup_path, "w:gz") as tar:
            for source_str in source_paths:
                source = Path(source_str)
                if not source.exists():
                    logger.warning(f"Source path does not exist, skipping: {source}")
                    continue
                
                arcname = source.name
                checksum = self._calculate_file_checksum(source)
                file_checksums[str(source)] = checksum
                tar.add(source, arcname=arcname)
        return file_checksums

    def _calculate_file_checksum(self, file_path: Path) -> str:
        """Calculates the SHA-256 checksum of a file."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(4096):
                sha256.update(chunk)
        return sha256.hexdigest()

    def restore_from_recovery_point(self, recovery_id: str, target_directory: str) -> bool:
        """
        Restores files from a recovery point to a target directory.

        Args:
            recovery_id: The ID of the recovery point to restore.
            target_directory: The directory to restore files into.

        Returns:
            True on successful restoration, False otherwise.
        """
        rp = self._get_recovery_point(recovery_id)
        if not rp or rp.status != RecoveryStatus.VALID:
            logger.error(f"Recovery point {recovery_id} is not valid for restore.")
            return False

        backup_path = Path(rp.backup_path)
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False

        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=target_directory)
            
            if not self._verify_restored_files(Path(target_directory), rp.file_checksums):
                raise ValueError("Checksum verification failed after restore.")
            
            logger.info(f"Successfully restored from recovery point {recovery_id}")
            return True
        except (tarfile.TarError, ValueError, IOError) as e:
            logger.error(f"Failed to restore from recovery point {recovery_id}: {e}")
            return False

    def _verify_restored_files(self, target_path: Path, checksums: Dict[str, str]) -> bool:
        """Verifies restored files against their original checksums."""
        for file_str, expected_checksum in checksums.items():
            original_path = Path(file_str)
            restored_path = target_path / original_path.name
            if not restored_path.exists():
                logger.error(f"Restored file missing: {restored_path}")
                return False
            actual_checksum = self._calculate_file_checksum(restored_path)
            if actual_checksum != expected_checksum:
                logger.error(f"Checksum mismatch for {restored_path}")
                return False
        return True
    
    def _get_recovery_point(self, recovery_id: str) -> Optional[RecoveryPoint]:
        """Retrieves a RecoveryPoint object from the database by its ID."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute("SELECT * FROM recovery_points WHERE recovery_id = ?", (recovery_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return RecoveryPoint(
                    recovery_id=row[0], name=row[1], description=row[2],
                    recovery_type=RecoveryPointType(row[3]),
                    created_at=datetime.fromisoformat(row[4]),
                    expires_at=datetime.fromisoformat(row[5]) if row[5] else None,
                    backup_path=row[6], compressed_size_bytes=row[7],
                    status=RecoveryStatus(row[8]),
                    metadata=json.loads(row[9] or "{}"),
                    file_checksums=json.loads(row[10] or "{}"),
                )
        except (sqlite3.Error, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to retrieve recovery point {recovery_id}: {e}")
            return None


class DocumentationTransactionManager:
    """Manages transactional operations with automatic rollback capabilities."""

    def __init__(self, backup_manager: DocumentationBackupManager):
        """
        Initializes the transaction manager.

        Args:
            backup_manager: An instance of DocumentationBackupManager.
        """
        self.backup_manager = backup_manager

    @contextlib.contextmanager
    def transaction(self, operation_name: str, watch_paths: List[str]):
        """
        A context manager for performing operations transactionally.

        Creates a pre-operation recovery point and automatically rolls back
        to it if an exception occurs within the `with` block.

        Args:
            operation_name: The name of the operation being performed.
            watch_paths: A list of file/directory paths to back up and monitor.

        Yields:
            The transaction object.

        Raises:
            Exception: Re-raises any exception that occurs within the block
                       after a rollback attempt.
        """
        recovery_id = self.backup_manager.create_recovery_point(
            name=f"Pre-operation: {operation_name}",
            description=f"Automatic backup before '{operation_name}'",
            source_paths=watch_paths,
            recovery_type=RecoveryPointType.PRE_OPERATION,
        )
        if not recovery_id:
            raise RuntimeError("Failed to create pre-operation recovery point. Aborting.")
        
        try:
            yield
        except Exception as e:
            logger.error(f"Transaction '{operation_name}' failed. Initiating rollback. Error: {e}")
            with tempfile.TemporaryDirectory() as temp_dir:
                restored = self.backup_manager.restore_from_recovery_point(recovery_id, temp_dir)
                if restored:
                    # Overwrite original files with restored versions
                    for source_path_str in watch_paths:
                        source_path = Path(source_path_str)
                        temp_source_path = Path(temp_dir) / source_path.name
                        if temp_source_path.exists():
                            shutil.copytree(temp_source_path, source_path, dirs_exist_ok=True) if source_path.is_dir() else shutil.copy2(temp_source_path, source_path)
                    logger.info("Rollback successful.")
                else:
                    logger.critical("ROLLBACK FAILED! System may be in an inconsistent state.")
            raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir_path = Path(temp_dir)
        backups_path = test_dir_path / "backups"
        docs_path = test_dir_path / "docs"
        docs_path.mkdir()

        (docs_path / "test1.md").write_text("# Original Content")

        backup_mgr = DocumentationBackupManager(str(backups_path))
        transaction_mgr = DocumentationTransactionManager(backup_mgr)

        logger.info("--- Testing successful transaction ---")
        try:
            with transaction_mgr.transaction("successful_edit", [str(docs_path)]):
                (docs_path / "test1.md").write_text("# Modified Content")
                logger.info("Modification complete inside transaction.")
            logger.info(f"Final content: '{(docs_path / 'test1.md').read_text()}'")
        except Exception as e:
            logger.error(f"Successful transaction failed unexpectedly: {e}")

        logger.info("\n--- Testing failed transaction (rollback) ---")
        try:
            with transaction_mgr.transaction("failed_edit", [str(docs_path)]):
                (docs_path / "test1.md").write_text("# This change will be rolled back")
                raise ValueError("Simulating a failure")
        except ValueError:
            logger.info("Caught expected failure.")
            logger.info(f"Content after rollback: '{(docs_path / 'test1.md').read_text()}'")