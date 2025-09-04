#!/usr/bin/env python3
"""
HUEY_P_Plugin_Development_Tools.py

Development tools for creating, testing, and managing documentation plugins.
Includes a development server with hot-reloading, a plugin validator,
and a scaffolding generator for creating new plugins.
"""

import argparse
import logging
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

# Assuming plugin_architecture is in the same path or a discoverable module
try:
    from plugin_architecture import PluginExecutionContext, PluginManager
except ImportError:
    print("Error: 'plugin_architecture.py' not found. Please ensure it's in the PYTHONPATH.")
    sys.exit(1)


logger = logging.getLogger(__name__)


class PluginDevelopmentServer:
    """
    A development server with hot-reloading for rapid plugin development.

    This server watches a specified plugin directory for changes and automatically
    reloads the affected plugin, allowing developers to see their changes
    without restarting the entire system.
    """

    def __init__(
        self, plugin_directory: str = "plugins_dev", output_directory: str = "dev_output"
    ):
        """
        Initializes the development server.

        Args:
            plugin_directory: The directory to watch for plugin source files.
            output_directory: A directory for test execution outputs.
        """
        self.plugin_directory = Path(plugin_directory)
        self.output_directory = Path(output_directory)
        self.plugin_manager: Optional[PluginManager] = None
        self.observer = Observer()
        self.is_running = False

        self.plugin_directory.mkdir(exist_ok=True)
        self.output_directory.mkdir(exist_ok=True)

    def start(self):
        """Starts the development server and file watcher."""
        logger.info("Starting plugin development server...")
        self.plugin_manager = PluginManager(plugin_directories=[str(self.plugin_directory)])
        self.plugin_manager.initialize()

        event_handler = PluginFileChangeHandler(self)
        self.observer.schedule(event_handler, str(self.plugin_directory), recursive=True)
        self.observer.start()
        self.is_running = True
        logger.info(f"Development server running. Watching: {self.plugin_directory}")

        try:
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stops the development server and file watcher."""
        logger.info("Stopping development server...")
        self.is_running = False
        self.observer.stop()
        self.observer.join()

    def reload_plugin(self, plugin_name: str):
        """
        Hot-reloads a specific plugin by disabling and re-enabling it.

        Args:
            plugin_name: The name of the plugin to reload.
        """
        if not self.plugin_manager:
            return

        logger.info(f"Hot-reloading plugin: {plugin_name}")
        try:
            if plugin_name in self.plugin_manager.enabled_plugins:
                self.plugin_manager.disable_plugin(plugin_name)

            self.plugin_manager.registry.discover_plugins()
            success = self.plugin_manager.enable_plugin(plugin_name)

            if success:
                logger.info(f"Successfully reloaded plugin: {plugin_name}")
                self._test_plugin_execution(plugin_name)
            else:
                logger.error(f"Failed to reload plugin: {plugin_name}")
        except Exception as e:
            logger.error(f"Error during plugin reload for '{plugin_name}': {e}", exc_info=True)

    def _test_plugin_execution(self, plugin_name: str):
        """Performs a quick test execution of a reloaded plugin."""
        if not self.plugin_manager:
            return

        logger.info(f"Performing post-reload test for {plugin_name}...")
        try:
            mock_context = PluginExecutionContext(
                parsed_sections={"6.1": {"title": "Test Section"}},
                plugin_config={},
                output_directory=self.output_directory / f"test_{plugin_name}",
                shared_data={},
                execution_id=f"test_{int(time.time())}",
                timestamp=datetime.now(),
            )
            results = self.plugin_manager.executor.execute_plugins([plugin_name], mock_context)
            if results.get(plugin_name, {}).get("status") == "success":
                logger.info(f"Plugin '{plugin_name}' test execution passed.")
            else:
                logger.warning(f"Plugin '{plugin_name}' test execution failed: {results}")
        except Exception as e:
            logger.error(f"Plugin test execution failed for '{plugin_name}': {e}", exc_info=True)


class PluginFileChangeHandler(FileSystemEventHandler):
    """Handles file system events for hot-reloading plugins."""

    def __init__(self, dev_server: PluginDevelopmentServer):
        self.dev_server = dev_server
        self.last_reload_time: Dict[str, float] = {}

    def on_modified(self, event):
        """
        Handles file modified events, triggering a plugin reload.

        Args:
            event: The watchdog event object.
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)
        if file_path.suffix != ".py" and file_path.name != "plugin.yaml":
            return

        plugin_name = self._get_plugin_name_from_path(file_path)
        if not plugin_name:
            return

        now = time.time()
        if now - self.last_reload_time.get(plugin_name, 0) < 2.0:
            return  # Debounce

        self.last_reload_time[plugin_name] = now
        logger.info(f"File changed: {file_path}")
        self.dev_server.reload_plugin(plugin_name)

    def _get_plugin_name_from_path(self, file_path: Path) -> Optional[str]:
        """Extracts the plugin name from its file path."""
        try:
            # Assumes structure is .../plugins_dev/plugin_name/
            return file_path.parent.name
        except IndexError:
            return None


class PluginGenerator:
    """Generates plugin scaffolding from templates."""

    def create_plugin(
        self, plugin_name: str, plugin_type: str, output_dir: str = "plugins"
    ) -> bool:
        """
        Creates a new plugin from a template.

        Args:
            plugin_name: The name for the new plugin (e.g., "my_new_plugin").
            plugin_type: The type of plugin ("document_generator", etc.).
            output_dir: The directory where the plugin folder will be created.

        Returns:
            True if the plugin was created successfully, False otherwise.
        """
        plugin_dir = Path(output_dir) / plugin_name
        try:
            plugin_dir.mkdir(parents=True, exist_ok=True)

            manifest = self._create_manifest(plugin_name, plugin_type)
            with open(plugin_dir / "plugin.yaml", "w") as f:
                yaml.dump(manifest, f, default_flow_style=False)

            class_name = "".join(word.capitalize() for word in plugin_name.split("_"))
            implementation = self._get_template().format(
                plugin_name=plugin_name, class_name=class_name
            )
            with open(plugin_dir / f"{plugin_name}.py", "w") as f:
                f.write(implementation)

            logger.info(f"Successfully created plugin '{plugin_name}' at: {plugin_dir}")
            return True
        except (IOError, OSError) as e:
            logger.error(f"Failed to create plugin '{plugin_name}': {e}")
            return False

    def _create_manifest(self, plugin_name: str, plugin_type: str) -> Dict:
        """Creates a manifest dictionary for a new plugin."""
        return {
            "name": plugin_name,
            "version": "1.0.0",
            "description": f"Auto-generated {plugin_type} plugin.",
            "author": "HUEY_P Development Team",
            "plugin_type": plugin_type,
            "dependencies": [],
            "supported_sections": ["*"],
            "output_formats": ["markdown"],
            "configuration_schema": {"properties": {"enabled": {"type": "boolean", "default": True}}},
            "min_core_version": "1.0.0",
        }

    def _get_template(self) -> str:
        """Returns the Python code template for a new plugin."""
        return """#!/usr/bin/env python3
\"\"\"
{plugin_name}.py

Auto-generated document generator plugin.
\"\"\"

from typing import Any, Dict, List
from plugin_architecture import (
    DocumentGeneratorPlugin,
    PluginExecutionContext,
    PluginMetadata,
    PluginType,
)

class {class_name}Plugin(DocumentGeneratorPlugin):
    \"\"\"Auto-generated plugin to demonstrate the architecture.\"\"\"

    def get_metadata(self) -> PluginMetadata:
        \"\"\"Returns the plugin's metadata.\"\"\"
        return PluginMetadata(
            name="{plugin_name}",
            version="1.0.0",
            description="An auto-generated plugin.",
            author="HUEY_P Developer",
            plugin_type=PluginType.DOCUMENT_GENERATOR,
            dependencies=[],
            supported_sections=["*"],
            output_formats=["markdown"],
            configuration_schema={{}},
            min_core_version="1.0.0",
        )

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        \"\"\"Validates the plugin's configuration.\"\"\"
        return []

    def initialize(self, config: Dict[str, Any]) -> bool:
        \"\"\"Initializes the plugin.\"\"\"
        self.config = config
        return True

    def generate_documents(self, context: PluginExecutionContext) -> List[str]:
        \"\"\"Generates documentation files.\"\"\"
        output_path = context.output_directory / "output.md"
        with open(output_path, "w") as f:
            f.write("# {plugin_name} Output\\n")
            f.write(f"Generated from section: {{list(context.parsed_sections.keys())[0]}}\\n")
        return [str(output_path)]

    def cleanup(self):
        \"\"\"Cleans up resources.\"\"\"
        pass
"""


def main():
    """Main function to run the command-line interface."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    parser = argparse.ArgumentParser(description="HUEY_P Plugin Development Tools")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create", help="Create a new plugin scaffold.")
    create_parser.add_argument("name", help="Plugin name (e.g., my_plugin).")
    create_parser.add_argument("--type", default="document_generator", help="Plugin type.")
    create_parser.add_argument("--output", default="plugins", help="Output directory.")

    dev_parser = subparsers.add_parser("dev", help="Start the hot-reloading development server.")
    dev_parser.add_argument("--plugins-dir", default="plugins_dev", help="Directory to watch.")
    dev_parser.add_argument("--output-dir", default="dev_output", help="Directory for test output.")

    args = parser.parse_args()

    if args.command == "create":
        generator = PluginGenerator()
        generator.create_plugin(args.name, args.type, args.output)
    elif args.command == "dev":
        dev_server = PluginDevelopmentServer(args.plugins_dir, args.output_dir)
        dev_server.start()


if __name__ == "__main__":
    main()