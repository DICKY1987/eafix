"""Configuration management for APF."""
from dataclasses import dataclass
from pathlib import Path
import os
import yaml

@dataclass
class AppConfig:
    registries_dir: Path
    defaults_yaml: Path
    stepkey_precision: int = 3

def load_config(repo_root: Path = None) -> AppConfig:
    root = repo_root or Path.cwd()
    user_cfg = Path.home() / ".huey-apf" / "config.yaml"
    defaults = root / "config" / "defaults.yaml"
    cfg = {"stepkey_precision": 3}
    if defaults.exists():
        cfg |= yaml.safe_load(defaults.read_text()) or {}
    if user_cfg.exists():
        cfg |= yaml.safe_load(user_cfg.read_text()) or {}
    return AppConfig(registries_dir=root / "registries", defaults_yaml=defaults, **cfg)
