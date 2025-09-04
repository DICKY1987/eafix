from pathlib import Path
import json
import pytest

jsonschema = pytest.importorskip("jsonschema")
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "src" / "eafix" / "schemas" / "diagnostics.schema.json"

VALID_EXAMPLES = [
    {
        "severity": "ERROR",
        "code": "APF0001",
        "message": "Unknown actor 'analyst' (did you mean 'user'?)",
        "location": {"file": "specs/demo_atomic.yaml", "line": 12, "column": 7},
    },
    {
        "severity": "WARN",
        "code": "APF0400",
        "message": "Importer ambiguity: sentence maps to multiple actions.",
        "location": {"file": "notes/process.md", "json_pointer": "/sections/2/paragraphs/3"},
        "data": {"candidates": ["normalize", "transform"]},
    },
]

INVALID_EXAMPLES = [
    {"severity": "FATAL", "code": "APF1", "message": "bad"},
    {"severity": "ERROR", "code": "APF9999", "message": "ok", "location": {"step_id": "abc"}},
]


def load_schema():
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_schema_validates_examples():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    for ex in VALID_EXAMPLES:
        validator.validate(ex)


def test_schema_rejects_invalid():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    for ex in INVALID_EXAMPLES:
        errors = list(validator.iter_errors(ex))
        assert errors, f"expected errors for: {ex}"


def test_stepkey_pattern():
    schema = load_schema()
    validator = Draft202012Validator(schema)
    ok = [
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "1.001"}},
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "12.0015"}},
    ]
    bad = [
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "1."}},
        {"severity": "INFO", "code": "APF0100", "message": "", "location": {"file": "x", "step_id": "a.b"}},
    ]
    for ex in ok:
        validator.validate(ex)
    for ex in bad:
        assert list(validator.iter_errors(ex))


def test_roundtrip_json():
    # Round‑trip encode/decode to ensure stability
    schema = load_schema()  # ensure file exists
    doc = VALID_EXAMPLES
    s = json.dumps(doc)
    doc2 = json.loads(s)
    assert doc2 == doc
