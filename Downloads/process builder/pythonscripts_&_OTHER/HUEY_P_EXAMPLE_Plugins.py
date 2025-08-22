#!/usr/bin/env python3
"""
HUEY_P_Plugin_Implementation_Examples.py

Example plugin implementations demonstrating the plugin architecture.
Shows how different documentation types can be created as isolated plugins.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

from plugin_architecture import (
    DocumentGeneratorPlugin,
    PluginExecutionContext,
    PluginMetadata,
    PluginType,
)


class DiagramGeneratorPlugin(DocumentGeneratorPlugin):
    """
    A plugin for generating system diagrams in various formats.

    This plugin can generate architecture, dataflow, and component diagrams
    from parsed specification sections. It supports multiple output formats like
    Mermaid and can create an interactive HTML viewer.
    """

    def get_metadata(self) -> PluginMetadata:
        """
        Returns the metadata for this plugin.

        Returns:
            A PluginMetadata object describing the plugin.
        """
        return PluginMetadata(
            name="diagram_generator",
            version="1.1.0",
            description="Generates system architecture and data flow diagrams",
            author="HUEY_P Visualization Team",
            plugin_type=PluginType.DIAGRAM_GENERATOR,
            dependencies=[],
            supported_sections=["6.*", "7.*", "10.*"],
            output_formats=["mermaid", "graphviz", "plantuml", "interactive_html"],
            configuration_schema={
                "properties": {
                    "output_format": {
                        "type": "string",
                        "enum": ["mermaid", "graphviz", "plantuml"],
                        "default": "mermaid",
                    },
                    "theme": {"type": "string", "default": "modern"},
                }
            },
            min_core_version="1.0.0",
        )

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """
        Validates the provided configuration for this plugin.

        Args:
            config: A dictionary containing the plugin's configuration.

        Returns:
            A list of error strings. An empty list signifies a valid config.
        """
        errors = []
        if config.get("output_format", "mermaid") not in [
            "mermaid",
            "graphviz",
            "plantuml",
        ]:
            errors.append("Invalid output_format specified.")
        return errors

    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initializes the plugin with a validated configuration.

        Args:
            config: The plugin's configuration dictionary.

        Returns:
            True if initialization is successful, False otherwise.
        """
        self.config = config
        self.output_format = config.get("output_format", "mermaid")
        return True

    def generate_documents(self, context: PluginExecutionContext) -> List[str]:
        """
        Generates all configured diagrams.

        Args:
            context: The execution context containing parsed data.

        Returns:
            A list of paths to the generated files.
        """
        generated_files = []
        arch_diagrams = self._generate_architecture_diagrams(context)
        generated_files.extend(arch_diagrams)
        return generated_files

    def _generate_architecture_diagrams(
        self, context: PluginExecutionContext
    ) -> List[str]:
        """Generates system architecture diagrams."""
        if self.output_format != "mermaid":
            return []

        arch_sections = {
            k: v for k, v in context.parsed_sections.items() if k.startswith("6.")
        }
        if not arch_sections:
            return []

        mermaid_content = self._create_mermaid_architecture(arch_sections)
        file_path = context.output_directory / "Architecture_Diagram.md"
        try:
            with open(file_path, "w") as f:
                f.write(f"# System Architecture Diagram\n\n")
                f.write(f"```mermaid\n{mermaid_content}\n```\n")
            return [str(file_path)]
        except IOError as e:
            print(f"Error writing diagram file: {e}")
            return []

    def _create_mermaid_architecture(self, arch_sections: Dict) -> str:
        """Creates the Mermaid syntax for an architecture diagram."""
        diagram = "graph TD\n    %% System Architecture\n"
        components = {}
        for section_data in arch_sections.values():
            if "components" in section_data:
                for comp_name, comp_data in section_data["components"].items():
                    components[comp_name] = {
                        "type": comp_data.get("type", "unknown"),
                        "dependencies": comp_data.get("dependencies", []),
                    }
        for name, info in components.items():
            style = {"service": "[{}]"}.get(info["type"], "({})")
            diagram += f"    {name}{style.format(name)}\n"
        for name, info in components.items():
            for dep in info.get("dependencies", []):
                if dep in components:
                    diagram += f"    {dep} --> {name}\n"
        return diagram

    def cleanup(self):
        """Cleans up resources used by the plugin."""
        pass


if __name__ == "__main__":
    from plugin_architecture import PluginManager

    # This is an example, typically plugins are not run directly.
    print("HUEY_P Plugin examples loaded.")
    # Initialize plugin manager
    plugin_manager = PluginManager()
    plugin_manager.initialize()