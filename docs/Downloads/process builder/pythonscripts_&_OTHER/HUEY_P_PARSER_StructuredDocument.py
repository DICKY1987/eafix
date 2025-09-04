#!/usr/bin/env python3
"""
HUEY_P_PY_Structured_Documentation_Parser.py

Converts structured English technical specifications to machine-readable formats.
Uses a finite component vocabulary to ensure consistent, parseable documentation.

This is the core of the "words to structured data" translation system.
"""

import json
import logging
import re
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)


class ComponentType(Enum):
    """Enumeration for the types of system components."""

    SERVICE = "service"
    INTERFACE = "interface"
    DATA_STORE = "data_store"
    EXTERNAL_SYSTEM = "external_system"
    OPERATIONAL_ELEMENT = "operational_element"


class SectionType(Enum):
    """Enumeration for the different layers/sections of the specification."""

    SERVICE_LAYER = "service_layer"
    INTERFACE_LAYER = "interface_layer"
    DATA_LAYER = "data_layer"
    DEPLOYMENT_LAYER = "deployment_layer"
    MONITORING_LAYER = "monitoring_layer"


@dataclass
class ComponentDefinition:
    """
    Structured definition of a system component.

    Attributes:
        name: The canonical name of the component.
        type: The type of the component, from ComponentType enum.
        dependencies: A list of component names this component depends on.
        interfaces: A list of interfaces exposed or used by this component.
        performance: A dictionary of performance requirements.
        configuration: A list of configuration items.
        health_monitoring: Description of health monitoring implementation.
        deployment_info: Dictionary containing deployment details.
    """

    name: str
    type: ComponentType
    dependencies: List[str]
    interfaces: List[str]
    performance: Dict[str, Any]
    configuration: List[str]
    health_monitoring: Optional[str] = None
    deployment_info: Optional[Dict[str, str]] = None


@dataclass
class SectionStructure:
    """
    Structured representation of a specification section.

    Attributes:
        section_id: The unique identifier for the section (e.g., "6.1").
        section_type: The type of the layer, from SectionType enum.
        title: The title of the section.
        components: A dictionary of component definitions within this section.
        layer_properties: A dictionary of properties applicable to the entire layer.
        relationships: A list of relationships between components.
        diagram_requirements: A list of diagrams to be generated for this section.
    """

    section_id: str
    section_type: SectionType
    title: str
    components: Dict[str, ComponentDefinition]
    layer_properties: Dict[str, Any]
    relationships: List[Dict[str, str]]
    diagram_requirements: List[str]


class ComponentVocabulary:
    """
    Manages the finite vocabulary of system components.

    Ensures that all components defined in the specification adhere to a known,
    validated set of terms, which is critical for automated parsing.
    """

    def __init__(self, vocabulary_file: str = None):
        """
        Initializes the component vocabulary manager.

        Args:
            vocabulary_file: Optional path to a YAML file defining the vocabulary.
                If not provided, a default vocabulary is loaded.
        """
        self.vocabulary = self._load_vocabulary(vocabulary_file)
        self.component_patterns = self._build_patterns()

    def _load_vocabulary(self, file_path: str) -> Dict:
        """
        Load component vocabulary from a YAML file.

        Args:
            file_path: The path to the vocabulary file.

        Returns:
            A dictionary representing the component vocabulary.
        """
        if file_path:
            try:
                with open(file_path, "r") as f:
                    return yaml.safe_load(f)
            except FileNotFoundError:
                logger.warning(f"Vocabulary file not found: {file_path}")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing vocabulary file {file_path}: {e}")

        # Default vocabulary
        return {
            "component_types": {
                "services": [
                    "SignalService",
                    "RiskService",
                    "AnalyticsService",
                    "MonitoringService",
                    "MarketDataService",
                    "ConfigurationService",
                ],
                "interfaces": [
                    "SocketBridge_DLL",
                    "REST_API",
                    "WebSocket_API",
                    "Named_Pipe",
                    "File_Interface",
                    "TCP_Socket",
                ],
                "data_stores": [
                    "SQLite_Database",
                    "Redis_Cache",
                    "CSV_Files",
                    "YAML_Configs",
                    "Health_Files",
                    "Heartbeat_Files",
                ],
                "external_systems": [
                    "MT4_Terminal",
                    "Expert_Advisors",
                    "Market_Data_Feed",
                    "Docker_Container",
                    "PowerShell_Scripts",
                ],
                "operational_elements": [
                    "Deployment_Scripts",
                    "Monitoring_Dashboards",
                    "Backup_Procedures",
                    "Security_Policies",
                    "Test_Suites",
                ],
            },
            "relationship_types": [
                "depends_on",
                "communicates_with",
                "configures",
                "monitors",
                "deploys_to",
                "secures",
                "validates",
                "logs_to",
            ],
            "property_types": {
                "performance": [
                    "latency_ms",
                    "throughput_rps",
                    "uptime_percentage",
                    "response_time_ms",
                ],
                "configuration": [
                    "config_file",
                    "environment_vars",
                    "runtime_parameters",
                ],
                "deployment": ["container_image", "script_path", "dependencies"],
            },
        }

    def _build_patterns(self) -> Dict[str, re.Pattern]:
        """
        Build regex patterns for parsing structured English.

        Returns:
            A dictionary of compiled regex patterns.
        """
        return {
            "section_template": re.compile(r""),
            "layer_type": re.compile(r"\*\*Layer Type:\*\* (\w+)"),
            "primary_components": re.compile(r"\*\*Primary Components:\*\* \[([^\]]+)\]"),
            "communication_interface": re.compile(
                r"\*\*Communication Interface:\*\* (\w+)"
            ),
            "data_dependencies": re.compile(r"\*\*Data Dependencies:\*\* \[([^\]]+)\]"),
            "performance_requirement": re.compile(r"(\w+): ([<>]=?\s*[\d.]+)"),
            "component_definition": re.compile(
                r"\*\*(\w+):\*\*\n((?:\s*- .*\n?)*)", re.MULTILINE
            ),
            "component_property": re.compile(r"- (\w+): (.+)"),
            "list_property": re.compile(r"- (\w+): \[([^\]]+)\]"),
        }

    def validate_component(self, component_name: str) -> bool:
        """
        Validate that a component exists in the vocabulary.

        Args:
            component_name: The name of the component to validate.

        Returns:
            True if the component is valid, False otherwise.
        """
        for components in self.vocabulary["component_types"].values():
            if component_name in components:
                return True
        return False

    def get_component_category(self, component_name: str) -> Optional[str]:
        """
        Get the category (e.g., services, interfaces) for a component.

        Args:
            component_name: The name of the component.

        Returns:
            The category name as a string, or None if not found.
        """
        for category, components in self.vocabulary["component_types"].items():
            if component_name in components:
                return category
        return None


class StructuredDocumentParser:
    """Parses structured English specifications into a machine-readable format."""

    def __init__(self, vocabulary: ComponentVocabulary):
        """
        Initializes the parser with a component vocabulary.

        Args:
            vocabulary: An instance of ComponentVocabulary.
        """
        self.vocabulary = vocabulary
        self.parsing_errors = []

    def parse_specification_document(
        self, file_path: str
    ) -> Dict[str, SectionStructure]:
        """
        Parse a complete specification document.

        Args:
            file_path: The path to the master technical specification file.

        Returns:
            A dictionary of parsed SectionStructure objects, keyed by section ID.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            logger.error(f"Specification document not found at: {file_path}")
            return {}
        except IOError as e:
            logger.error(f"Error reading specification document {file_path}: {e}")
            return {}

        sections = {}
        section_pattern = re.compile(
            r"## (\d+\.[\d\.]*)\s+([^\n]+)\n(.*?)(?=\n## \d+\.|\n\Z)",
            re.DOTALL | re.MULTILINE,
        )

        for match in section_pattern.finditer(content):
            section_id = match.group(1)
            title = match.group(2).strip()
            section_content = match.group(3)

            if "