#!/usr/bin/env python3
"""
HUEY_P_PY_Document_Automation_System.py

Automated system for maintaining synchronization between the Master Technical
Specification (source of truth), derived component tables, and visual diagrams.

Author: HUEY_P Development Team
Version: 1.1.0
Created: 2025-07-04
"""

import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger(__name__)


@dataclass
class ComponentDefinition:
    """
    Structured component definition extracted from the specification document.

    Attributes:
        name: The canonical name of the component.
        type: The type of the component (e.g., "Service", "DLL").
        layer: The architectural layer the component belongs to.
        description: A brief description of the component's purpose.
        performance: Performance requirements or SLAs.
        communication: The communication protocol used.
        sub_components: A list of sub-components.
        dependencies: A list of components this component depends on.
        interfaces: A dictionary of exposed interfaces.
        health_monitoring: A dictionary defining health check mechanisms.
        configuration: A list of configuration items.
        file_path: The source file path for the component.
        section_number: The document section number defining the component.
    """

    name: str
    type: str
    layer: str
    description: str
    performance: Optional[str] = None
    communication: Optional[str] = None
    sub_components: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    interfaces: Dict[str, str] = field(default_factory=dict)
    health_monitoring: Dict[str, str] = field(default_factory=dict)
    configuration: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    section_number: Optional[str] = None


class DocumentParser:
    """Extracts structured component definitions from the Master Technical Spec."""

    def __init__(self, spec_file_path: str):
        """
        Initializes the DocumentParser.

        Args:
            spec_file_path: The path to the master specification file.
        """
        self.spec_file_path = spec_file_path
        self.component_pattern = re.compile(
            r"(.*?)",
            re.DOTALL | re.MULTILINE,
        )

    def extract_components(self) -> Dict[str, ComponentDefinition]:
        """
        Extracts all component definitions from the document.

        Returns:
            A dictionary of ComponentDefinition objects, keyed by component name.
        """
        try:
            with open(self.spec_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"Specification file not found: {self.spec_file_path}")
            return {}

        components = {}
        for match in self.component_pattern.finditer(content):
            name, text = match.groups()
            component = self._parse_component_text(name, text.strip())
            if component:
                components[name] = component
        return components

    def _parse_component_text(self, name: str, text: str) -> Optional[ComponentDefinition]:
        """Parses the text block of a single component definition."""
        properties = {}
        for line in text.split("\n"):
            if ":" in line:
                key, value = (part.strip() for part in line.split(":", 1))
                key = key.strip("*")
                properties[key] = value

        try:
            return ComponentDefinition(
                name=name,
                type=properties.get("Type", "Unknown"),
                layer=properties.get("Layer", "Unknown"),
                description=properties.get("Description", ""),
                dependencies=properties.get("Dependencies", "").split(", ")
                if properties.get("Dependencies")
                else [],
            )
        except KeyError as e:
            logger.error(f"Component '{name}' is missing required field: {e}")
            return None


class TableGenerator:
    """Generates Markdown tables from parsed component definitions."""

    def generate_component_matrix(
        self, components: Dict[str, ComponentDefinition]
    ) -> str:
        """
        Generates the main component matrix as a Markdown table.

        Args:
            components: A dictionary of component definitions.

        Returns:
            A string containing the Markdown table.
        """
        header = "| Component | Type | Layer | Dependencies |\n|:---|:---|:---|:---|\n"
        rows = [
            f"| {c.name} | {c.type} | {c.layer} | {', '.join(c.dependencies) or 'None'} |"
            for c in components.values()
        ]
        return header + "\n".join(rows)


class DocumentUpdater:
    """Updates the Master Technical Specification with auto-generated tables."""

    def __init__(self, spec_file_path: str):
        """
        Initializes the DocumentUpdater.

        Args:
            spec_file_path: The path to the master specification file.
        """
        self.spec_file_path = spec_file_path

    def update_tables(self, tables: Dict[str, str]) -> bool:
        """
        Updates all auto-generated tables in the document.

        Args:
            tables: A dictionary of table markdown, keyed by table name.

        Returns:
            True if the update was successful, False otherwise.
        """
        try:
            with open(self.spec_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            logger.error(f"Could not read specification file for update: {e}")
            return False

        updated_content = content
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for name, markdown in tables.items():
            section = f"""{markdown}
"""
            pattern = re.compile(
                f".*?",
                re.DOTALL,
            )
            if re.search(pattern, updated_content):
                updated_content = re.sub(pattern, section, updated_content)
            else:
                logger.warning(f"Table placeholder '{name}' not found in document.")

        try:
            with open(self.spec_file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)
            return True
        except IOError as e:
            logger.error(f"Could not write to specification file: {e}")
            return False


class AutomationChangeHandler(FileSystemEventHandler):
    """Monitors the specification file and triggers updates on change."""

    def __init__(self, system: "DocumentAutomationSystem"):
        """
        Initializes the change handler.

        Args:
            system: The DocumentAutomationSystem instance to trigger.
        """
        self.system = system
        self.last_hash = ""

    def on_modified(self, event):
        """
        Handles the file modified event.

        Args:
            event: The watchdog event object.
        """
        if not event.is_directory and event.src_path.endswith(".md"):
            current_hash = self._calculate_file_hash(event.src_path)
            if current_hash != self.last_hash:
                logger.info(f"Change detected in: {event.src_path}")
                self.system.process_document_change()
                self.last_hash = current_hash

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculates the SHA-256 hash of a file's content."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except IOError:
            return ""


class DocumentAutomationSystem:
    """Main orchestrator for the document automation workflow."""

    def __init__(self, spec_file_path: str):
        """
        Initializes the automation system.

        Args:
            spec_file_path: Path to the Master Technical Specification.
        """
        self.spec_file_path = spec_file_path
        self.parser = DocumentParser(spec_file_path)
        self.table_generator = TableGenerator()
        self.document_updater = DocumentUpdater(spec_file_path)
        self.observer = Observer()
        self.change_handler = AutomationChangeHandler(self)

    def start_monitoring(self):
        """Starts monitoring the specification file for changes."""
        watch_dir = str(Path(self.spec_file_path).parent)
        self.observer.schedule(self.change_handler, watch_dir, recursive=False)
        self.observer.start()
        logger.info(f"Started monitoring: {self.spec_file_path}")

    def stop_monitoring(self):
        """Stops the file monitoring."""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped monitoring.")

    def process_document_change(self):
        """Processes detected changes in the specification document."""
        logger.info("Processing document changes...")
        components = self.parser.extract_components()
        if not components:
            logger.warning("No components extracted, aborting update.")
            return

        tables = {"ComponentMatrix": self.table_generator.generate_component_matrix(components)}
        if self.document_updater.update_tables(tables):
            logger.info("Successfully updated document tables.")
        else:
            logger.error("Failed to update document tables.")


def main():
    """Main execution function for the Document Automation System."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    spec_file = "Master Technical Specification.md"
    system = DocumentAutomationSystem(spec_file)

    # Perform one initial processing run
    system.process_document_change()

    # Start monitoring for file changes
    system.start_monitoring()
    try:
        while True:
            pass  # Keep the main thread alive
    except KeyboardInterrupt:
        system.stop_monitoring()


if __name__ == "__main__":
    main()