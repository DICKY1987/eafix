#!/usr/bin/env python3
"""
HUEY_P_PY_Documentation_Ecosystem_Orchestrator.py

Complete orchestration system for the living documentation ecosystem.
Manages bidirectional synchronization between the Master Technical Specification
and all downstream documentation artifacts.
"""

import hashlib
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Assumes roadmap_automation is available and corrected
from roadmap_automation import RoadmapGenerator, TimelineGenerator

logger = logging.getLogger(__name__)


class ChangeType(Enum):
    """Enumeration for the type of change detected in the specification."""

    SECTION_MODIFIED = "section_modified"
    # Additional change types can be added here
    # SECTION_ADDED = "section_added"
    # SECTION_DELETED = "section_deleted"


class ArtifactType(Enum):
    """Enumeration for the types of artifacts that can be generated."""

    ROADMAP = "roadmap"
    API_DOCS = "api_docs"
    TEST_SPECS = "test_specs"
    DEPLOYMENT_SCRIPTS = "deployment_scripts"
    DIAGRAMS = "diagrams"


@dataclass
class SectionMetadata:
    """
    Metadata for a numbered section in the Master Technical Specification.

    Attributes:
        section_id: The unique identifier for the section (e.g., "6.1").
        title: The title of the section.
        last_modified: Timestamp of the last modification.
        content_hash: SHA-256 hash of the section's content.
        dependencies: List of other section IDs this section depends on.
        dependents: List of other section IDs that depend on this one.
        generates_artifacts: List of artifact types generated from this section.
    """

    section_id: str
    title: str
    last_modified: datetime
    content_hash: str
    dependencies: List[str]
    dependents: List[str]
    generates_artifacts: List[ArtifactType]


@dataclass
class ChangeEvent:
    """
    Represents a detected change in the specification.

    Attributes:
        timestamp: When the change was detected.
        change_type: The type of change.
        section_id: The ID of the affected section.
        required_artifacts: A list of artifact types that need regeneration.
        priority: The priority of the change ("Critical", "High", etc.).
    """

    timestamp: datetime
    change_type: ChangeType
    section_id: str
    required_artifacts: List[ArtifactType]
    priority: str


class SectionTracker:
    """Tracks changes to individual sections in the specification."""

    def __init__(self, spec_file_path: str):
        """
        Initializes the SectionTracker.

        Args:
            spec_file_path: Path to the Master Technical Specification.
        """
        self.spec_file_path = spec_file_path
        self.section_metadata: Dict[str, SectionMetadata] = {}

    def extract_section_metadata(self) -> Dict[str, SectionMetadata]:
        """
        Extracts metadata for all sections from the specification file.

        Returns:
            A dictionary of SectionMetadata objects, keyed by section ID.
        """
        try:
            with open(self.spec_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"Specification file not found: {self.spec_file_path}")
            return {}

        section_pattern = re.compile(
            r"## (\d+\.[\d\.]*)\s+([^\n]+)\n(.*?)(?=\n## \d+\.|\n\Z)",
            re.DOTALL | re.MULTILINE,
        )
        metadata = {}
        for match in section_pattern.finditer(content):
            section_id, title, section_content = match.groups()
            meta = self._parse_section_metadata(section_id, title, section_content)
            metadata[section_id] = meta

        self.section_metadata = metadata
        self._build_dependency_graph()
        return metadata

    def _parse_section_metadata(
        self, section_id: str, title: str, content: str
    ) -> SectionMetadata:
        """Parses metadata from a single section's content."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        dep_refs = re.findall(r"Section (\d+\.[\d\.]*)", content)
        artifacts = self._determine_generated_artifacts(section_id)
        return SectionMetadata(
            section_id=section_id, title=title.strip(),
            last_modified=datetime.now(), content_hash=content_hash,
            dependencies=list(set(dep_refs)), dependents=[],
            generates_artifacts=artifacts,
        )

    def _determine_generated_artifacts(self, section_id: str) -> List[ArtifactType]:
        """Determines which artifacts are generated from a given section."""
        artifacts = [ArtifactType.DIAGRAMS]
        if section_id.startswith("6."):
            artifacts.append(ArtifactType.ROADMAP)
        if section_id.startswith("11."):
            artifacts.extend([ArtifactType.API_DOCS, ArtifactType.TEST_SPECS])
        if section_id.startswith("15."):
            artifacts.append(ArtifactType.DEPLOYMENT_SCRIPTS)
        return artifacts

    def _build_dependency_graph(self):
        """Calculates and populates the `dependents` field for each section."""
        for section_id, metadata in self.section_metadata.items():
            for dep_id in metadata.dependencies:
                if dep_id in self.section_metadata:
                    self.section_metadata[dep_id].dependents.append(section_id)

    def detect_changes(
        self, previous_metadata: Dict[str, SectionMetadata]
    ) -> List[ChangeEvent]:
        """
        Detects changes between current and previous specification metadata.

        Args:
            previous_metadata: A dictionary of the last known section metadata.

        Returns:
            A list of ChangeEvent objects representing detected changes.
        """
        changes = []
        for section_id, current_meta in self.section_metadata.items():
            previous_meta = previous_metadata.get(section_id)
            if not previous_meta or current_meta.content_hash != previous_meta.content_hash:
                changes.append(
                    ChangeEvent(
                        timestamp=datetime.now(),
                        change_type=ChangeType.SECTION_MODIFIED,
                        section_id=section_id,
                        required_artifacts=current_meta.generates_artifacts,
                        priority="High" if section_id.startswith("6.") else "Medium",
                    )
                )
        return changes


class ArtifactGenerator:
    """Generates downstream artifacts from specification changes."""

    def __init__(self, output_dir: str):
        """
        Initializes the ArtifactGenerator.

        Args:
            output_dir: The root directory for all generated artifacts.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        for artifact_type in ArtifactType:
            (self.output_dir / artifact_type.value).mkdir(exist_ok=True)

    def generate_artifacts(
        self,
        change_events: List[ChangeEvent],
        section_metadata: Dict[str, SectionMetadata],
    ) -> Dict[str, List[str]]:
        """
        Generates all required artifacts based on a list of change events.

        Args:
            change_events: A list of changes that triggered the generation.
            section_metadata: The full, current metadata of all sections.

        Returns:
            A dictionary mapping artifact types to a list of generated file paths.
        """
        generation_results: Dict[str, List[str]] = {}
        artifacts_to_generate = {
            artifact for change in change_events for artifact in change.required_artifacts
        }

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_map = {
                executor.submit(
                    self._generate_single_artifact, at, section_metadata
                ): at
                for at in artifacts_to_generate
            }
            for future in future_map:
                artifact_type = future_map[future]
                try:
                    result = future.result(timeout=60)
                    generation_results[artifact_type.value] = result
                except Exception as e:
                    logger.error(f"Failed to generate {artifact_type.value}: {e}", exc_info=True)
                    generation_results[artifact_type.value] = [f"Error: {e}"]
        return generation_results

    def _generate_single_artifact(
        self, artifact_type: ArtifactType, metadata: Dict[str, SectionMetadata]
    ) -> List[str]:
        """Dispatcher function to generate a specific type of artifact."""
        if artifact_type == ArtifactType.ROADMAP:
            return self._generate_roadmap()
        # Add other artifact generation calls here
        return []

    def _generate_roadmap(self) -> List[str]:
        """Generates the implementation roadmap and timeline."""
        # This assumes the spec file path is known or passed differently
        roadmap_gen = RoadmapGenerator("Master Technical Specification.md")
        phases = roadmap_gen.extract_development_phases()
        timeline_gen = TimelineGenerator()
        timeline = timeline_gen.generate_timeline(phases)
        gantt_markdown = timeline_gen.generate_gantt_markdown(timeline)
        
        roadmap_file = self.output_dir / "roadmap/HUEY_P_Implementation_Roadmap.md"
        timeline_file = self.output_dir / "roadmap/HUEY_P_Project_Timeline.json"
        
        try:
            with open(roadmap_file, "w") as f:
                f.write(gantt_markdown)
            with open(timeline_file, "w") as f:
                json.dump(timeline, f, indent=2)
            return [str(roadmap_file), str(timeline_file)]
        except IOError as e:
            logger.error(f"Error writing roadmap files: {e}")
            return []


class DocumentationEcosystem:
    """Main orchestrator for the complete documentation ecosystem."""

    def __init__(
        self,
        spec_file_path: str,
        output_dir: str = "output",
    ):
        """
        Initializes the DocumentationEcosystem.

        Args:
            spec_file_path: Path to the Master Technical Specification.
            output_dir: The root directory for generated artifacts.
        """
        self.spec_file_path = spec_file_path
        self.section_tracker = SectionTracker(spec_file_path)
        self.artifact_generator = ArtifactGenerator(output_dir)
        self.previous_metadata: Dict[str, SectionMetadata] = {}
        self.observer = Observer()

    def initialize(self) -> bool:
        """
        Initializes the ecosystem and performs an initial generation run.

        Returns:
            True if initialization was successful, False otherwise.
        """
        logger.info("Initializing HUEY_P Documentation Ecosystem...")
        try:
            self.previous_metadata = self.section_tracker.extract_section_metadata()
            logger.info(f"Extracted metadata for {len(self.previous_metadata)} sections.")
            # Trigger initial generation for all sections
            initial_changes = [
                ChangeEvent(
                    datetime.now(), ChangeType.SECTION_MODIFIED,
                    section_id, meta.generates_artifacts, "Medium"
                )
                for section_id, meta in self.previous_metadata.items()
            ]
            self.process_changes(initial_changes)
            logger.info("Initial artifact generation complete.")
            return True
        except Exception as e:
            logger.error(f"Ecosystem initialization failed: {e}", exc_info=True)
            return False

    def start_monitoring(self):
        """Starts monitoring the specification file for changes."""
        watch_dir = str(Path(self.spec_file_path).parent)
        event_handler = DocumentChangeHandler(self)
        self.observer.schedule(event_handler, watch_dir, recursive=False)
        self.observer.start()
        logger.info(f"Started monitoring: {self.spec_file_path}")

    def stop_monitoring(self):
        """Stops monitoring for changes."""
        self.observer.stop()
        self.observer.join()
        logger.info("Stopped monitoring.")

    def process_file_change(self):
        """Processes detected changes in the specification file."""
        logger.info("Processing file change...")
        current_metadata = self.section_tracker.extract_section_metadata()
        changes = self.section_tracker.detect_changes(self.previous_metadata)
        
        if changes:
            logger.info(f"Detected {len(changes)} changes.")
            self.process_changes(changes)
            self.previous_metadata = current_metadata
        else:
            logger.info("No significant changes detected.")
            
    def process_changes(self, changes: List[ChangeEvent]):
        """Generates artifacts based on a list of changes."""
        if not changes:
            return
        self.artifact_generator.generate_artifacts(changes, self.section_metadata)


class DocumentChangeHandler(FileSystemEventHandler):
    """Handles file system events for the specification document."""

    def __init__(self, ecosystem: DocumentationEcosystem):
        self.ecosystem = ecosystem
        self.last_triggered = 0.0

    def on_modified(self, event):
        """Handles the file modified event with debouncing."""
        if not event.is_directory and event.src_path.endswith(".md"):
            # Debounce to avoid rapid firing
            now = time.time()
            if now - self.last_triggered > 2.0:
                self.last_triggered = now
                self.ecosystem.process_file_change()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    ecosystem = DocumentationEcosystem(spec_file_path="Master Technical Specification.md", output_dir="ecosystem_output")
    if ecosystem.initialize():
        ecosystem.start_monitoring()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            ecosystem.stop_monitoring()