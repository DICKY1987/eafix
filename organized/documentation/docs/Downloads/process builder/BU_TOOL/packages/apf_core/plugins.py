from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

@dataclass
class PluginContext:
    root: Path = Path(".")
    workdir: Path = Path(".")

class PluginError(Exception):
    pass

class Result(dict):
    """Simple success envelope."""
    @staticmethod
    def ok(**kwargs) -> "Result":
        r = Result(kwargs)
        r["ok"] = True
        return r

    @staticmethod
    def fail(message: str, **kwargs) -> "Result":
        r = Result(kwargs)
        r["ok"] = False
        r["error"] = message
        return r