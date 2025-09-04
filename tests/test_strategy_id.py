from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))
import strategy_id


def test_strategy_id_deterministic():
    base = strategy_id.generate("US", "High")
    again = strategy_id.generate("US", "High")
    assert base == again


def test_anticipation_offset():
    base = strategy_id.generate("US", "High")
    ant = strategy_id.generate("US", "High", anticipation=True)
    assert ant == base + 1000
