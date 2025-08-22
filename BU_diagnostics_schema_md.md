# Diagnostics Schema & Testing

> Standardized diagnostic format and testing infrastructure for error reporting and validation.

## Diagnostics JSON Schema

The schema should be placed at `schemas/diagnostics.schema.json`:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://schemas.apf.local/diagnostics.schema.json",
  "title": "APF Diagnostics",
  "description": "Structured diagnostics from APF tools (validation, import, export).",
  "type": "array",
  "items": { "$ref": "#/$defs/Diagnostic" },
  "$defs": {
    "Severity": {
      "type": "string",
      "description": "Severity of the diagnostic.",
      "enum": ["ERROR", "WARN", "INFO"]
    },
    "Location": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "file": { 
          "type": "string", 
          "description": "Source file path related to the diagnostic." 
        },
        "step_id": {
          "type": "string",
          "description": "Optional APF StepKey impacted by this diagnostic.",
          "pattern": "^\\d+(\\.\\d{3,})?$"
        },
        "json_pointer": { 
          "type": "string", 
          "description": "JSON Pointer into the source document, if applicable." 
        },
        "line": { "type": "integer", "minimum": 1 },
        "column": { "type": "integer", "minimum": 1 }
      }
    },
    "Diagnostic": {
      "type": "object",
      "additionalProperties": false,
      "required": ["severity", "code", "message"],
      "properties": {
        "severity": { "$ref": "#/$defs/Severity" },
        "code": {
          "type": "string",
          "description": "Stable diagnostic code.",
          "pattern": "^APF[0-9]{4}$"
        },
        "message": { 
          "type": "string", 
          "minLength": 1, 
          "maxLength": 2000 
        },
        "location": { "$ref": "#/$defs/Location" },
        "related": {
          "type": "array",
          "description": "Related StepKeys or file references.",
          "items": {
            "type": "string"
          },
          "uniqueItems": true
        },
        "hint": { 
          "type": "string", 
          "description": "Optional remediation guidance." 
        },
        "run_id": { 
          "type": "string", 
          "description": "Correlates diagnostics across artifacts." 
        },
        "timestamp": { 
          "type": "string", 
          "format": "date-time" 
        },
        "data": { 
          "type": "object", 
          "description": "Free-form structured context for tooling.", 
          "additionalProperties": true 
        }
      }
    }
  },
  "examples": [
    [
      {
        "severity": "ERROR",
        "code": "APF0001",
        "message": "Unknown actor 'analyst' (did you mean 'user'?)",
        "location": { 
          "file": "specs/demo_atomic.yaml", 
          "line": 12, 
          "column": 7 
        },
        "hint": "Add alias in registries/actors.yaml or change the author field.",
        "run_id": "2025-08-22T01:23:45Z#abc123"
      },
      {
        "severity": "WARN",
        "code": "APF0400",
        "message": "Importer ambiguity: sentence maps to multiple actions.",
        "location": { 
          "file": "notes/process.md", 
          "json_pointer": "/sections/2/paragraphs/3" 
        },
        "data": { "candidates": ["normalize", "transform"] }
      }
    ]
  ]
}
```

## Diagnostic Code Standards

### Code Format
- Pattern: `APF####` where `####` is a 4-digit number
- Range allocation:
  - `APF0001-APF0999`: Core validation errors
  - `APF1000-APF1999`: Import/parsing errors  
  - `APF2000-APF2999`: Export errors
  - `APF3000-APF3999`: Plugin system errors
  - `APF4000-APF4999`: Sequencing/StepKey errors
  - `APF5000-APF5999`: Watch loop/orchestration errors

### Severity Guidelines
- **ERROR**: Blocks export/processing; must be fixed
- **WARN**: Allows processing but indicates potential issues
- **INFO**: Advisory information for user awareness

### Location Context
- **file**: Source file path (relative to project root)
- **step_id**: StepKey pattern `\d+(\.\d{3,})?` (e.g., "1.001", "2.0015")
- **json_pointer**: RFC 6901 JSON Pointer for precise location
- **line/column**: 1-based indexing for text files

## Unit Tests & Validation

### Registry Validation Tests
Place at `tests/unit/test_registries.py`:

```python
import pytest
import yaml
from pathlib import Path
from jsonschema import validate, ValidationError

def test_actors_registry_shape():
    """Validate actors.yaml has required structure and no duplicates."""
    actors_path = Path("registries/actors.yaml")
    assert actors_path.exists(), "actors.yaml missing"
    
    with open(actors_path) as f:
        data = yaml.safe_load(f)
    
    # Check top-level structure
    assert "actors" in data
    assert isinstance(data["actors"], list)
    
    # Check for duplicates
    ids = [actor["id"] for actor in data["actors"]]
    assert len(ids) == len(set(ids)), "Duplicate actor IDs found"
    
    # Validate each actor entry
    for actor in data["actors"]:
        assert "id" in actor
        assert "name" in actor
        assert isinstance(actor["id"], str)
        assert len(actor["id"]) > 0
        assert actor["id"].islower()  # Enforce lowercase IDs

def test_actions_registry_shape():
    """Validate actions.yaml has required structure and canonical forms."""
    actions_path = Path("registries/actions.yaml")
    assert actions_path.exists(), "actions.yaml missing"
    
    with open(actions_path) as f:
        data = yaml.safe_load(f)
    
    assert "actions" in data
    assert isinstance(data["actions"], list)
    
    # Check for duplicates in canonical forms
    canonical_forms = [action["canonical"] for action in data["actions"]]
    assert len(canonical_forms) == len(set(canonical_forms)), "Duplicate canonical actions"
    
    # Validate structure
    for action in data["actions"]:
        assert "canonical" in action
        assert isinstance(action["canonical"], str)
        if "aliases" in action:
            assert isinstance(action["aliases"], list)
```

### Diagnostics Schema Tests
Place at `tests/unit/test_diagnostics_schema.py`:

```python
import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path

@pytest.fixture
def diagnostics_schema():
    schema_path = Path("schemas/diagnostics.schema.json")
    with open(schema_path) as f:
        return json.load(f)

def test_valid_diagnostic_example(diagnostics_schema):
    """Test that example diagnostics validate against schema."""
    valid_diagnostics = [
        {
            "severity": "ERROR",
            "code": "APF0001",
            "message": "Unknown actor 'analyst'",
            "location": {
                "file": "specs/demo.yaml",
                "line": 12,
                "column": 7,
                "step_id": "1.001"
            },
            "hint": "Add to registries/actors.yaml",
            "run_id": "test-run-123"
        }
    ]
    
    # Should not raise ValidationError
    validate(instance=valid_diagnostics, schema=diagnostics_schema)

def test_invalid_diagnostic_code(diagnostics_schema):
    """Test that invalid diagnostic codes are rejected."""
    invalid_diagnostics = [
        {
            "severity": "ERROR",
            "code": "INVALID",  # Wrong format
            "message": "Test message"
        }
    ]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_diagnostics, schema=diagnostics_schema)

def test_step_id_pattern(diagnostics_schema):
    """Test StepKey pattern validation in diagnostics."""
    # Valid StepKey patterns
    valid_step_ids = ["1.001", "2.0015", "10.100"]
    
    for step_id in valid_step_ids:
        diagnostic = [{
            "severity": "INFO", 
            "code": "APF0000",
            "message": "Test",
            "location": {"step_id": step_id}
        }]
        validate(instance=diagnostic, schema=diagnostics_schema)
    
    # Invalid StepKey pattern
    invalid_diagnostic = [{
        "severity": "INFO",
        "code": "APF0000", 
        "message": "Test",
        "location": {"step_id": "invalid"}
    }]
    
    with pytest.raises(ValidationError):
        validate(instance=invalid_diagnostic, schema=diagnostics_schema)

def test_roundtrip_json(diagnostics_schema):
    """Test JSON round-trip stability."""
    doc = [
        {
            "severity": "ERROR",
            "code": "APF0001", 
            "message": "Test error",
            "location": {"file": "test.yaml"}
        }
    ]
    s = json.dumps(doc)
    doc2 = json.loads(s)
    assert doc2 == doc
    validate(instance=doc2, schema=diagnostics_schema)
```

## CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
name: CI
on: [push, pull_request]

jobs:
  test-registries:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'
      
      - name: Install dependencies
        run: |
          python -m pip install -U pip
          python -m pip install .[dev]
      
      - name: Test registries
        run: |
          pytest tests/unit/test_registries.py -v
      
      - name: Test diagnostics schema
        run: |
          pytest tests/unit/test_diagnostics_schema.py -v
      
      - name: Validate all schemas
        run: |
          python -m jsonschema schemas/atomic_process.schema.json
          python -m jsonschema schemas/diagnostics.schema.json
          python -m jsonschema schemas/plugin.manifest.schema.json
```

## Integration with Core Components

### Validation Pipeline
1. **Input → Schema Validation** → Structural diagnostics
2. **Schema Valid → Semantic Validation** → Business rule diagnostics  
3. **Diagnostics → Editor/CLI** → User feedback with precise locations

### Usage in Core Modules
- **`apf_core/validation/diagnostics.py`** - Rich diagnostic types with NDJSON emission
- **`apf_core/validation/validator.py`** - Schema + semantic validation using diagnostic format
- **CLI/Desktop editors** - Parse diagnostics for error panels and quick-fixes

### Key Dependencies
- **JSONSchema validation** for schema compliance
- **Registry lookups** for actor/action validation
- **StepKey parsing** for location context
- **Run correlation** for audit trails

This infrastructure ensures that the foundational contracts (registries and schemas) remain valid and consistent as the system evolves.