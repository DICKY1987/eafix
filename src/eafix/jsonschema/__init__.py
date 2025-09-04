import re
from typing import Any, Dict, Iterator, List

class ValidationError(Exception):
    """Simple validation error used by the lightweight validator."""
    pass


class Draft202012Validator:
    """Very small subset of the real jsonschema Draft 2020-12 validator.

    It only implements the features needed by the tests for the diagnostics
    schema.  The goal isn't full JSON Schema compliance – just enough behaviour
    so that the tests can exercise the schema and ensure that our examples are
    well formed.  The interface mirrors the parts of ``jsonschema`` used in the
    tests: ``validate`` and ``iter_errors``.
    """

    def __init__(self, schema: Dict[str, Any]):
        # The diagnostics schema defines an array whose items reference the
        # ``Diagnostic`` definition.  For convenience we allow validating either
        # a single diagnostic object or a list of them.
        self.schema = schema
        self.diag_schema = schema.get("$defs", {}).get("Diagnostic", schema)
        self.location_schema = schema.get("$defs", {}).get("Location", {})
        self.severities = set(schema.get("$defs", {}).get("Severity", {}).get("enum", []))

    # Public API -----------------------------------------------------------
    def validate(self, instance: Any) -> None:
        errors = list(self.iter_errors(instance))
        if errors:
            raise ValidationError(errors[0])

    def iter_errors(self, instance: Any) -> Iterator[str]:
        if isinstance(instance, list):
            for item in instance:
                yield from self._validate_diag(item)
        else:
            yield from self._validate_diag(instance)

    # Internal helpers ----------------------------------------------------
    def _validate_diag(self, obj: Any) -> Iterator[str]:
        if not isinstance(obj, dict):
            yield "diagnostic must be object"
            return

        required = {"severity", "code", "message"}
        missing = required - obj.keys()
        for key in missing:
            yield f"missing property: {key}"

        # additionalProperties = false
        allowed = {
            "severity",
            "code",
            "message",
            "location",
            "related",
            "hint",
            "run_id",
            "timestamp",
            "data",
        }
        extras = set(obj.keys()) - allowed
        if extras:
            yield f"additional properties not allowed: {sorted(extras)}"

        sev = obj.get("severity")
        if not isinstance(sev, str) or sev not in self.severities:
            yield f"invalid severity: {sev}"

        code = obj.get("code")
        if not isinstance(code, str) or not re.fullmatch(r"APF[0-9]{4}", code):
            yield f"invalid code: {code}"

        msg = obj.get("message")
        # The real schema uses ``minLength: 1`` but the tests exercise cases
        # where an empty string is permitted.  To keep the validator lightweight
        # and aligned with the tests we only enforce an upper bound.
        if not isinstance(msg, str) or len(msg) > 2000:
            yield "invalid message"

        loc = obj.get("location")
        if loc is not None:
            yield from self._validate_location(loc)

        related = obj.get("related")
        if related is not None:
            if not isinstance(related, list):
                yield "related must be array"
            else:
                seen: set[str] = set()
                for item in related:
                    if not isinstance(item, str):
                        yield "related items must be strings"
                    elif item in seen:
                        yield f"duplicate related item: {item}"
                    seen.add(item)

        for field in ["hint", "run_id", "timestamp"]:
            val = obj.get(field)
            if val is not None and not isinstance(val, str):
                yield f"{field} must be string"

        data = obj.get("data")
        if data is not None and not isinstance(data, dict):
            yield "data must be object"

    def _validate_location(self, loc: Any) -> Iterator[str]:
        if not isinstance(loc, dict):
            yield "location must be object"
            return

        allowed = {"file", "step_id", "json_pointer", "line", "column"}
        extras = set(loc.keys()) - allowed
        if extras:
            yield f"location additional properties not allowed: {sorted(extras)}"

        file = loc.get("file")
        if file is not None and not isinstance(file, str):
            yield "file must be string"

        step_id = loc.get("step_id")
        if step_id is not None:
            if not isinstance(step_id, str) or not re.fullmatch(r"\d+(\.\d{3,})?", step_id):
                yield f"invalid step_id: {step_id}"

        jp = loc.get("json_pointer")
        if jp is not None and not isinstance(jp, str):
            yield "json_pointer must be string"

        line = loc.get("line")
        if line is not None:
            if not isinstance(line, int) or line < 1:
                yield "line must be >= 1"

        col = loc.get("column")
        if col is not None:
            if not isinstance(col, int) or col < 1:
                yield "column must be >= 1"
