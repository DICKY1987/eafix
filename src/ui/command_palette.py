"""Command palette implementation providing fuzzy search and quick actions.

The implementation is intentionally lightweight and self-contained so it can be
used in small demos and unit tests.  Only a subset of the behaviour of the full
application is implemented, but the public API mirrors what a real command
palette might expose.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

try:  # pragma: no cover - optional dependency
    import customtkinter as ctk  # type: ignore
except Exception:  # pragma: no cover - fallback to tkinter widgets
    # customtkinter is not available in the execution environment used for the
    # kata.  Provide a very small subset of the API required by the command
    # palette using standard tkinter widgets.
    class _Dummy(tk.Frame):
        def __init__(self, *a, **kw):  # pragma: no cover - trivial
            super().__init__(*a, **kw)

    class _DummyTop(tk.Toplevel):
        pass

    class _DummyScrollable(tk.Frame):
        pass

    class _DummySlider(tk.Scale):
        def __init__(self, master=None, **kwargs):  # pragma: no cover
            kwargs.setdefault("orient", tk.HORIZONTAL)
            super().__init__(master, **kwargs)

    class _DummyFont:
        def __init__(self, *a, **kw):
            pass

    ctk = type(
        "ctk",
        (),
        {
            "CTk": tk.Tk,
            "CTkFrame": tk.Frame,
            "CTkLabel": tk.Label,
            "CTkEntry": tk.Entry,
            "CTkButton": tk.Button,
            "CTkToplevel": _DummyTop,
            "CTkScrollableFrame": _DummyScrollable,
            "CTkSlider": _DummySlider,
            "CTkFont": _DummyFont,
        },
    )

from core.event_bus import event_bus
from core.state_manager import state_manager
from themes.colors import ColorPalette
from .toast_manager import show_info, show_warning


# ---------------------------------------------------------------------------
# Command data structures and fuzzy matching helpers


@dataclass
class Command:
    """Command definition used by the palette."""

    id: str
    title: str
    description: str
    category: str
    keywords: List[str]
    callback: Callable
    shortcut: Optional[str] = None
    enabled: bool = True
    risk_gated: bool = False


class FuzzyMatcher:
    """Very small fuzzy matcher based on character inclusion."""

    @staticmethod
    def score_match(query: str, text: str) -> float:
        query = query.lower()
        text = text.lower()
        if not query:
            return 1.0
        if query == text:
            return 1.0
        if query in text:
            return len(query) / len(text)
        # sequential character match
        it = iter(text)
        matched = sum(1 for ch in query if ch in it)
        return matched / max(len(text), 1)

    @staticmethod
    def find_matches(query: str, items: List[str], threshold: float = 0.1) -> List[Tuple[str, float]]:
        matches: List[Tuple[str, float]] = []
        for item in items:
            score = FuzzyMatcher.score_match(query, item)
            if score >= threshold:
                matches.append((item, score))
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches


# ---------------------------------------------------------------------------
# Command registry


class CommandRegistry:
    """Registry storing available commands grouped by category."""

    def __init__(self) -> None:
        self.commands: Dict[str, Command] = {}
        self.categories: Dict[str, List[str]] = {}
        self._register_default_commands()

    def register_command(self, command: Command) -> None:
        self.commands[command.id] = command
        self.categories.setdefault(command.category, []).append(command.id)

    def unregister_command(self, command_id: str) -> None:
        if command_id in self.commands:
            cat = self.commands[command_id].category
            self.categories.get(cat, []).remove(command_id)
            del self.commands[command_id]

    def get_command(self, command_id: str) -> Optional[Command]:
        return self.commands.get(command_id)

    # searching -------------------------------------------------------------
    def search_commands(self, query: str, limit: int = 10) -> List[Command]:
        searchable: Dict[str, str] = {}
        for cmd_id, cmd in self.commands.items():
            if not cmd.enabled:
                continue
            if cmd.risk_gated and not state_manager.is_action_allowed()[0]:
                continue
            searchable[cmd_id] = f"{cmd.title} {cmd.description} {' '.join(cmd.keywords)}"
        items = list(searchable.values())
        ids = list(searchable.keys())
        results = FuzzyMatcher.find_matches(query, items)
        found: List[Command] = []
        for item, _score in results[:limit]:
            idx = items.index(item)
            found.append(self.commands[ids[idx]])
        return found

    # default commands -----------------------------------------------------
    def _register_default_commands(self) -> None:
        self.register_command(
            Command(
                id="data_refresh_all",
                title="Refresh All Data",
                description="Force refresh of all market data",
                category="Data",
                keywords=["refresh", "update"],
                callback=lambda: event_bus.publish("force_data_refresh", {}, "command_palette"),
            )
        )
        self.register_command(
            Command(
                id="settings_theme",
                title="Toggle Theme",
                description="Switch between dark and light themes",
                category="Settings",
                keywords=["toggle", "theme"],
                callback=lambda: event_bus.publish("toggle_theme", {}, "command_palette"),
            )
        )


# ---------------------------------------------------------------------------
# Palette widgets


class CommandPaletteWidget(ctk.CTkToplevel):
    """Popup window displaying the command palette."""

    def __init__(self, master, command_registry: CommandRegistry):  # pragma: no cover - UI code
        super().__init__(master)
        self.command_registry = command_registry
        self.current_commands: List[Command] = []
        self.selected_index = 0
        self.title("Command Palette")
        self.geometry("600x400")
        self.configure(bg=ColorPalette.DARK_SURFACE)
        self.transient(master)
        self.grab_set()
        self.setup_ui()
        self.perform_search("")

    def setup_ui(self) -> None:  # pragma: no cover - UI code
        main = ctk.CTkFrame(self, fg_color=ColorPalette.DARK_SURFACE_VARIANT)
        main.pack(fill="both", expand=True, padx=5, pady=5)
        self.search_entry = ctk.CTkEntry(main)
        self.search_entry.pack(fill="x", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)
        self.results = ctk.CTkScrollableFrame(main)
        self.results.pack(fill="both", expand=True, padx=10, pady=10)
        self.status_label = ctk.CTkLabel(main, text="")
        self.status_label.pack(fill="x", padx=10, pady=(0, 10))

    def on_search_changed(self, _event=None) -> None:  # pragma: no cover - UI code
        self.perform_search(self.search_entry.get())

    def perform_search(self, query: str) -> None:
        self.current_commands = self.command_registry.search_commands(query, limit=20)
        self.selected_index = 0
        self.update_results()
        self.status_label.configure(text=f"Found {len(self.current_commands)} commands")

    def update_results(self) -> None:  # pragma: no cover - UI code
        for widget in list(self.results.winfo_children()):
            widget.destroy()
        for idx, cmd in enumerate(self.current_commands):
            frame = ctk.CTkFrame(self.results, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            label = ctk.CTkLabel(frame, text=cmd.title, anchor="w")
            label.pack(fill="x")
            frame.bind("<Button-1>", lambda e, c=cmd: self.execute_command(c))
            label.bind("<Button-1>", lambda e, c=cmd: self.execute_command(c))

    def execute_command(self, command: Command) -> None:
        try:
            command.callback()
            event_bus.publish(
                "command_executed",
                {"command_id": command.id, "command_title": command.title, "timestamp": datetime.now().isoformat()},
                "command_palette",
            )
            show_info(f"Executed: {command.title}")
        except Exception as exc:  # pragma: no cover - defensive
            show_warning(f"Failed to execute command: {exc}")
        finally:
            self.destroy()


# ---------------------------------------------------------------------------
# Manager


class CommandPaletteManager:
    """High level API to show the command palette."""

    def __init__(self, main_window) -> None:  # pragma: no cover - UI heavy
        self.main_window = main_window
        self.command_registry = CommandRegistry()
        self.current_palette: Optional[CommandPaletteWidget] = None

    def toggle_palette(self) -> None:  # pragma: no cover - UI heavy
        if self.current_palette and self.current_palette.winfo_exists():
            self.current_palette.destroy()
            self.current_palette = None
        else:
            self.current_palette = CommandPaletteWidget(self.main_window, self.command_registry)

    def register_command(self, command: Command) -> None:
        self.command_registry.register_command(command)

    def unregister_command(self, command_id: str) -> None:
        self.command_registry.unregister_command(command_id)

    def get_registry(self) -> CommandRegistry:
        return self.command_registry


# Global manager used by convenience helpers
command_palette_manager: Optional[CommandPaletteManager] = None


def initialize_command_palette(main_window) -> CommandPaletteManager:  # pragma: no cover - UI setup
    global command_palette_manager
    command_palette_manager = CommandPaletteManager(main_window)
    return command_palette_manager


def show_command_palette() -> None:  # pragma: no cover - UI code
    if command_palette_manager:
        command_palette_manager.toggle_palette()


def register_command(command: Command) -> None:
    if command_palette_manager:
        command_palette_manager.register_command(command)


__all__ = [
    "Command",
    "FuzzyMatcher",
    "CommandRegistry",
    "CommandPaletteWidget",
    "CommandPaletteManager",
    "initialize_command_palette",
    "show_command_palette",
    "register_command",
]
