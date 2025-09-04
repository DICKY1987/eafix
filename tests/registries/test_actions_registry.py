import re
from pathlib import Path

import pytest
yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parents[2]
ACTIONS = ROOT / "src" / "eafix" / "registries" / "actions.yaml"

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def test_actions_registry_structure():
    data = yaml.safe_load(ACTIONS.read_text(encoding="utf-8"))
    assert isinstance(data.get("version"), int) and data["version"] >= 1

    categories = data.get("categories")
    assert isinstance(categories, dict) and categories

    style = data.get("diagram_style")
    assert isinstance(style, dict) and style
    # Style must define at least all categories
    assert set(categories.keys()).issubset(set(style.keys()))

    actions = data.get("actions")
    assert isinstance(actions, list) and actions

    seen_ids = set()
    seen_aliases = set()

    for a in actions:
        assert set(a.keys()).issubset({"id", "label", "category", "description", "synonyms", "notes"})
        aid = a.get("id"); label = a.get("label"); cat = a.get("category")
        assert isinstance(aid, str) and ID_RE.match(aid), f"bad id: {aid!r}"
        assert aid not in seen_ids, f"duplicate action id: {aid}"
        seen_ids.add(aid)
        assert isinstance(label, str) and label
        assert cat in categories, f"unknown category for {aid}: {cat}"

        # synonyms optional but if present, must be unique and non‑colliding
        syn = a.get("synonyms", []) or []
        assert isinstance(syn, list)
        for s in syn:
            assert isinstance(s, str) and s
            assert s not in seen_ids, f"synonym collides with existing action id: {s}"
            assert s not in seen_aliases, f"duplicate synonym across actions: {s}"
            seen_aliases.add(s)
