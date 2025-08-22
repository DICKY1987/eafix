#!/usr/bin/env python3
"""
HUEY_P Master Data Management Solution

Provides a unified data governance framework to serve as a single source of
truth across all system components. Includes schema evolution, data quality
validation, and a unified access layer.
"""

import json
import logging
import re
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import redis

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Enumeration for the types of data sources."""
    TRANSACTIONAL = "transactional"
    CACHE = "cache"
    MASTER = "master"


class DataQualityRule(Enum):
    """Enumeration for data quality validation rule types."""
    NOT_NULL = "not_null"
    RANGE_CHECK = "range_check"
    FORMAT_VALIDATION = "format_validation"


@dataclass
class DataDefinition:
    """
    Defines the master schema for a piece of data.

    Attributes:
        name: The canonical name of the data element.
        data_type: The fundamental type of the data (e.g., "object", "string").
        source_type: The primary source of this data.
        validation_rules: A list of rules to enforce data quality.
        dependencies: A list of other data definitions this one depends on.
        version: The version of this data definition.
    """
    name: str
    data_type: str
    source_type: DataSourceType
    validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    version: str = "1.0"


class MasterDataRegistry:
    """A central registry for all data definitions across the system."""

    def __init__(self, registry_db_path: str):
        """
        Initializes the MasterDataRegistry.

        Args:
            registry_db_path: The path to the SQLite database for the registry.
        """
        self.db_path = registry_db_path
        self.definitions: Dict[str, DataDefinition] = {}
        self._initialize_registry()

    def _initialize_registry(self):
        """Initializes the master data registry database schema."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS data_definitions (
                        name TEXT PRIMARY KEY, definition TEXT, version TEXT,
                        created_at TEXT, updated_at TEXT
                    )
                    """
                )
        except sqlite3.Error as e:
            logger.critical(f"Registry database initialization failed: {e}")
            raise
        self._load_existing_definitions()

    def _load_existing_definitions(self):
        """Loads all existing data definitions from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT name, definition FROM data_definitions")
                for row in cursor.fetchall():
                    name, definition_json = row
                    definition_dict = json.loads(definition_json)
                    # Re-create the object, handling the enum
                    definition_dict["source_type"] = DataSourceType(definition_dict["source_type"])
                    self.definitions[name] = DataDefinition(**definition_dict)
        except (sqlite3.Error, json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to load existing data definitions: {e}")


class DataQualityValidator:
    """Validates data against registered quality rules."""

    def validate_data(
        self, definition: DataDefinition, data_value: Any
    ) -> List[str]:
        """
        Validates a piece of data against its definition's quality rules.

        Args:
            definition: The DataDefinition for the data being validated.
            data_value: The actual data value to validate.

        Returns:
            A list of string descriptions of any validation failures.
        """
        violations = []
        for rule in definition.validation_rules:
            rule_type = DataQualityRule(rule["type"])
            if rule_type == DataQualityRule.NOT_NULL and data_value is None:
                violations.append(f"Field '{definition.name}' cannot be null.")
            elif rule_type == DataQualityRule.FORMAT_VALIDATION:
                pattern = rule.get("pattern")
                if pattern and not re.match(pattern, str(data_value)):
                    violations.append(f"Value '{data_value}' does not match pattern '{pattern}'.")
        return violations


class MasterDataManager:
    """
    Main orchestrator for master data management.

    This class provides a unified interface for defining, validating,
    and accessing data across the entire system.
    """

    def __init__(self, registry_db_path: str = "master_data_registry.db"):
        """
        Initializes the MasterDataManager.

        Args:
            registry_db_path: Path to the SQLite database for the registry.
        """
        self.registry = MasterDataRegistry(registry_db_path)
        self.validator = DataQualityValidator()
        self._register_core_definitions()

    def _register_core_definitions(self):
        """Registers the core data definitions essential for the HUEY_P system."""
        defs = [
            DataDefinition(
                name="trading_signal", data_type="object",
                source_type=DataSourceType.TRANSACTIONAL,
                validation_rules=[{"type": "not_null"}],
            ),
            DataDefinition(
                name="market_data", data_type="object",
                source_type=DataSourceType.CACHE,
                validation_rules=[
                    {"type": "not_null"},
                    {"type": "format_validation", "pattern": r"^[A-Z]{3,6}$"},
                ],
            ),
        ]
        for definition in defs:
            if definition.name not in self.registry.definitions:
                self.registry.definitions[definition.name] = definition


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    mdm = MasterDataManager()
    logger.info(f"Loaded {len(mdm.registry.definitions)} data definitions.")

    # Example: Validate a piece of data
    signal_def = mdm.registry.definitions.get("trading_signal")
    if signal_def:
        valid_signal = {"signal_id": "SIG_001", "symbol": "AAPL"}
        invalid_signal = None
        
        violations = mdm.validator.validate_data(signal_def, valid_signal)
        logger.info(f"Validation for valid signal: {'OK' if not violations else violations}")

        violations = mdm.validator.validate_data(signal_def, invalid_signal)
        logger.info(f"Validation for invalid signal: {'OK' if not violations else violations}")