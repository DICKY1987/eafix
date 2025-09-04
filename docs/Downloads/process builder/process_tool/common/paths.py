"""Repository path helpers for APF."""
from dataclasses import dataclass
from pathlib import Path

@dataclass
class RepoPaths:
    root: Path
    derived: Path
    schemas: Path
    registries: Path

    @classmethod
    def discover(cls, start: Path = None) -> "RepoPaths":
        cur = (start or Path.cwd()).resolve()
        for p in [cur, *cur.parents]:
            if (p / "pyproject.toml").exists():
                return cls(root=p, derived=p / "derived", schemas=p / "schemas", registries=p / "registries")
        raise RuntimeError("Repo root not found (missing pyproject.toml)")
