import re
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
ACTORS = ROOT / "registries" / "actors.yaml"

ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
KINDS = {"HUMAN", "CORE", "PLUGIN", "SERVICE", "STORAGE"}


def test_actors_registry_structure():
    data = yaml.safe_load(ACTORS.read_text(encoding="utf-8"))
    assert isinstance(data.get("version"), int) and data["version"] >= 1

    lanes = data.get("lanes")
    assert isinstance(lanes, dict) and lanes

    actors = data.get("actors")
    assert isinstance(actors, list) and actors

    seen_ids = set()
    seen_aliases = set()

    for a in actors:
        assert set(a.keys()).issubset({"id", "label", "kind", "lane", "description", "aliases"})
        aid = a.get("id"); kind = a.get("kind"); lane = a.get("lane")
        assert isinstance(aid, str) and ID_RE.match(aid), f"bad id: {aid!r}"
        assert aid not in seen_ids, f"duplicate actor id: {aid}"
        seen_ids.add(aid)
        assert kind in KINDS, f"unknown kind for {aid}: {kind}"
        assert lane in lanes, f"unknown lane for {aid}: {lane}"
        assert isinstance(a.get("label"), str) and a["label"]
        assert isinstance(a.get("description"), str) and a["description"]

        aliases = a.get("aliases", []) or []
        assert isinstance(aliases, list)
        for s in aliases:
            assert isinstance(s, str) and s
            assert s not in seen_ids, f"alias collides with actor id: {s}"
            assert s not in seen_aliases, f"duplicate alias across actors: {s}"
            seen_aliases.add(s)
