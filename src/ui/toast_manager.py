"""Tiny helper functions for user notifications.

The original project likely implements a sophisticated toast/notification
system.  For test purposes we simply print the messages to stdout.  Returning the
message makes the functions easy to assert in unit tests if ever required.
"""

from __future__ import annotations

from typing import Any


def show_info(message: str) -> str:
    print(message)
    return message


def show_warning(message: str) -> str:
    print(f"WARNING: {message}")
    return message

__all__ = ["show_info", "show_warning"]
