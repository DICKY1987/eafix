from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import List, Optional


def load_indicators_from_dir(directory: Path, category: Optional[str] = None) -> List[object]:
    """Load indicator instances from JSON configs in *directory*.

    Each JSON file must define at minimum a ``class`` key with the fully
    qualified class name.  Optional ``args`` provide keyword arguments.  A
    ``config_class`` + ``config`` pair may be supplied to instantiate and pass a
    dataclass-style configuration object.  ``category`` can be used to filter
    which configs are loaded.
    """
    indicators: List[object] = []
    for cfg_path in sorted(directory.glob("*.json")):
        data = json.loads(cfg_path.read_text(encoding="utf-8"))
        if category and data.get("category") != category:
            continue
        module_name, class_name = data["class"].rsplit(".", 1)
        cls = getattr(importlib.import_module(module_name), class_name)
        kwargs = data.get("args", {}).copy()
        cfg_cls_path = data.get("config_class")
        if cfg_cls_path:
            cfg_module, cfg_name = cfg_cls_path.rsplit(".", 1)
            cfg_cls = getattr(importlib.import_module(cfg_module), cfg_name)
            cfg_args = data.get("config", {})
            kwargs["cfg"] = cfg_cls(**cfg_args)
        indicators.append(cls(**kwargs))
    return indicators

