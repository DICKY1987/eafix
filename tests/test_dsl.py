import pathlib
import sys
import pytest

# Allow running tests without installing the package
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from eafix.guardian.constraints.dsl import evaluate


def test_evaluate_boolean_expression():
    context = {"x": 2, "y": 5}
    assert evaluate("x < 5 and y >= 5", context) is True
    assert evaluate("x > 10 or y < 3", context) is False


def test_evaluate_rejects_unsafe_expression():
    # Attempting to access builtins or call functions should fail
    assert evaluate("__import__('os').system('echo hi')", {}) is False
    assert evaluate("(lambda: 1)()", {}) is False
