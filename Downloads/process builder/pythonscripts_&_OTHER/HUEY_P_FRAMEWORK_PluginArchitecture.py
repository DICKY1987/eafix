#!/usr/bin/env python3
"""
HUEY_P_PY_Plugin_Architecture_Framework.py

A plugin-based documentation generation system that allows for modular extension.
This framework provides the core capabilities for plugin discovery, loading,
execution, and management.
"""

import importlib.util
import inspect
import json
import logging
import sys
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import yaml

logger = logging.getLogger(__name__)


class PluginStatus(Enum):
    """Enumeration for the lifecycle status of a plugin."""

    LOADED = "loaded"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class PluginType(Enum):
    """Enumeration for the functional type of a plugin."""

    DOCUMENT_GENERATOR = "document_generator"
    DIAGRAM_GENERATOR = "diagram_generator"
    VALIDATOR = "validator"
    TRANSFORMER = "transformer"
    EXPORTER = "exporter"


@dataclass
class PluginMetadata:
    """
    Metadata for plugin registration and management.

    Attributes:
        name: The unique name of the plugin.
        version: The semantic version of the plugin.
        description: A brief description of the plugin's purpose.
        author: The author or team responsible for the plugin.
        plugin_type: The functional type of the plugin.
        dependencies: A list of other plugin names this plugin depends on.
        supported_sections: List of specification sections this plugin processes.
        output_formats: List of output formats this plugin can generate.
        configuration_schema: A JSON schema for the plugin's configuration.
        min_core_version: The minimum core system version required.
        max_core_version: The maximum compatible core system version.
        tags: A list of tags for categorization.
        license: The license under which the plugin is distributed.
        homepage: The URL for the plugin's homepage or repository.
    """

    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str]
    supported_sections: List[str]
    output_formats: List[str]
    configuration_schema: Dict[str, Any]
    min_core_version: str
    max_core_version: Optional[str] = None
    tags: Optional[List[str]] = None
    license: str = "MIT"
    homepage: str = ""


@dataclass
class PluginExecutionContext:
    """
    Context provided to a plugin during its execution.

    Attributes:
        parsed_sections: A dictionary of parsed data from the source document.
        plugin_config: The configuration specific to the executing plugin.
        output_directory: The base directory for plugin output files.
        shared_data: A dictionary for sharing data between plugins.
        execution_id: A unique ID for this execution run.
        timestamp: The timestamp of the execution run.
    """

    parsed_sections: Dict[str, Any]
    plugin_config: Dict[str, Any]
    output_directory: Path
    shared_data: Dict[str, Any]
    execution_id: str
    timestamp: datetime


class PluginInterface(ABC):
    """Abstract base class that all plugins must implement."""

    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """
        Return the plugin's metadata.

        Returns:
            A PluginMetadata object.
        """
        pass

    @abstractmethod
    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate the plugin's configuration.

        Args:
            config: The configuration dictionary to validate.

        Returns:
            A list of error messages. An empty list indicates success.
        """
        pass

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize the plugin with its configuration.

        Args:
            config: The plugin-specific configuration dictionary.

        Returns:
            True if initialization was successful, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, context: PluginExecutionContext) -> Dict[str, Any]:
        """
        Execute the main logic of the plugin.

        Args:
            context: The execution context containing shared data and config.

        Returns:
            A dictionary containing the results of the execution.
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Clean up any resources used by the plugin."""
        pass


class DocumentGeneratorPlugin(PluginInterface):
    """Base class for plugins that generate documentation files."""

    @abstractmethod
    def generate_documents(self, context: PluginExecutionContext) -> List[str]:
        """
        Generate documents based on the provided context.

        Args:
            context: The execution context.

        Returns:
            A list of file paths for the generated documents.
        """
        pass

    def execute(self, context: PluginExecutionContext) -> Dict[str, Any]:
        """
        Executes the document generation logic.

        Args:
            context: The execution context.

        Returns:
            A dictionary containing the status and a list of generated files.
        """
        try:
            generated_files = self.generate_documents(context)
            return {
                "status": "success",
                "generated_files": generated_files,
                "plugin_name": self.get_metadata().name,
            }
        except Exception as e:
            logger.error(f"Plugin {self.get_metadata().name} failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "plugin_name": self.get_metadata().name,
            }


class PluginRegistry:
    """Manages the discovery and registration of available plugins."""

    def __init__(self, plugin_directories: Optional[List[str]] = None):
        """
        Initializes the PluginRegistry.

        Args:
            plugin_directories: A list of directories to search for plugins.
        """
        self.plugin_directories = plugin_directories or ["plugins"]
        self.registered_plugins: Dict[str, PluginMetadata] = {}
        self.loaded_plugins: Dict[str, PluginInterface] = {}
        self.plugin_statuses: Dict[str, PluginStatus] = {}

    def discover_plugins(self):
        """Discovers plugins in the configured directories."""
        for plugin_dir in self.plugin_directories:
            plugin_path = Path(plugin_dir)
            if not plugin_path.exists():
                continue

            for manifest_file in plugin_path.glob("**/plugin.yaml"):
                try:
                    with open(manifest_file, "r") as f:
                        manifest_data = yaml.safe_load(f)
                    metadata = PluginMetadata(
                        name=manifest_data["name"],
                        version=manifest_data["version"],
                        description=manifest_data["description"],
                        author=manifest_data["author"],
                        plugin_type=PluginType(manifest_data["plugin_type"]),
                        dependencies=manifest_data.get("dependencies", []),
                        supported_sections=manifest_data.get("supported_sections", ["*"]),
                        output_formats=manifest_data.get("output_formats", []),
                        configuration_schema=manifest_data.get(
                            "configuration_schema", {}
                        ),
                        min_core_version=manifest_data["min_core_version"],
                    )
                    self.register_plugin(metadata)
                except (IOError, yaml.YAMLError, KeyError, ValueError) as e:
                    logger.error(f"Error loading manifest {manifest_file}: {e}")

    def register_plugin(self, metadata: PluginMetadata):
        """
        Manually registers a plugin.

        Args:
            metadata: The PluginMetadata object to register.
        """
        self.registered_plugins[metadata.name] = metadata
        self.plugin_statuses[metadata.name] = PluginStatus.LOADED


class PluginLoader:
    """Handles the dynamic loading and unloading of plugin implementations."""

    def __init__(self, registry: PluginRegistry):
        """
        Initializes the PluginLoader.

        Args:
            registry: The PluginRegistry to interact with.
        """
        self.registry = registry

    def load_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """
        Loads a plugin's implementation from its source file.

        Args:
            plugin_name: The name of the plugin to load.

        Returns:
            An instance of the plugin class, or None if loading fails.
        """
        metadata = self.registry.registered_plugins.get(plugin_name)
        if not metadata:
            logger.error(f"Plugin '{plugin_name}' not found in registry.")
            return None

        try:
            module_path = self._find_plugin_module(plugin_name)
            if not module_path:
                raise FileNotFoundError(f"Implementation file for {plugin_name} not found.")

            spec = importlib.util.spec_from_file_location(
                f"plugin_{plugin_name}", module_path
            )
            if not spec or not spec.loader:
                raise ImportError(f"Could not create module spec for {plugin_name}.")

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"plugin_{plugin_name}"] = module
            spec.loader.exec_module(module)

            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                 raise AttributeError(f"No plugin class found in {module_path}")

            instance = plugin_class()
            self.registry.loaded_plugins[plugin_name] = instance
            self.registry.plugin_statuses[plugin_name] = PluginStatus.LOADED
            logger.info(f"Successfully loaded plugin: {plugin_name}")
            return instance

        except (FileNotFoundError, ImportError, AttributeError, TypeError) as e:
            logger.error(f"Error loading plugin {plugin_name}: {e}")
            self.registry.plugin_statuses[plugin_name] = PluginStatus.ERROR
            return None

    def _find_plugin_module(self, plugin_name: str) -> Optional[Path]:
        """Finds the main Python module file for a given plugin."""
        for plugin_dir in self.registry.plugin_directories:
            for candidate in Path(plugin_dir).rglob(f"{plugin_name}.py"):
                return candidate
        return None

    def _find_plugin_class(self, module: Any) -> Optional[type]:
        """Finds the class implementing PluginInterface in a module."""
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, PluginInterface) and obj is not PluginInterface:
                return obj
        return None


class PluginExecutor:
    """Executes plugins concurrently with error isolation."""

    def __init__(self, registry: PluginRegistry, max_workers: int = 4):
        """
        Initializes the PluginExecutor.

        Args:
            registry: The PluginRegistry containing loaded plugins.
            max_workers: The maximum number of threads for concurrent execution.
        """
        self.registry = registry
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def execute_plugins(
        self, plugin_names: List[str], context: PluginExecutionContext
    ) -> Dict[str, Dict[str, Any]]:
        """
        Executes a list of plugins concurrently.

        Args:
            plugin_names: A list of names of plugins to execute.
            context: The execution context to pass to each plugin.

        Returns:
            A dictionary of execution results, keyed by plugin name.
        """
        active_plugins = [
            name
            for name in plugin_names
            if self.registry.plugin_statuses.get(name) == PluginStatus.ACTIVE
        ]
        futures: Dict[str, Future] = {
            name: self.executor.submit(self._execute_single, name, context)
            for name in active_plugins
        }
        results = {}
        for name, future in futures.items():
            try:
                results[name] = future.result(timeout=300)
            except Exception as e:
                logger.error(f"Plugin {name} execution failed: {e}")
                results[name] = {"status": "error", "error": str(e)}
        return results

    def _execute_single(
        self, plugin_name: str, context: PluginExecutionContext
    ) -> Dict[str, Any]:
        """Executes a single plugin with error handling."""
        try:
            plugin = self.registry.loaded_plugins[plugin_name]
            plugin_context = PluginExecutionContext(
                parsed_sections=context.parsed_sections,
                plugin_config=context.plugin_config, # Simplified for example
                output_directory=context.output_directory / plugin_name,
                shared_data=context.shared_data.copy(),
                execution_id=f"{context.execution_id}_{plugin_name}",
                timestamp=context.timestamp,
            )
            plugin_context.output_directory.mkdir(exist_ok=True, parents=True)
            return plugin.execute(plugin_context)
        except Exception as e:
            logger.error(f"Error executing plugin {plugin_name}: {traceback.format_exc()}")
            return {"status": "error", "error": str(e)}

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # This file is a framework and not meant to be executed directly.
    # See plugin_examples.py for usage.
    logger.info("Plugin Architecture Framework loaded.")