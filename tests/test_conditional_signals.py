import csv
from pathlib import Path

import pytest

from eafix.conditional_signals import (
    ConditionalRow,
    ConditionalScanner,
    ScanConfig,
    state_rsi_bucket,
    state_none,
    pips,
)


def test_state_helpers():
    assert state_rsi_bucket(20) == "RSI_0_30"
    assert state_rsi_bucket(50) == "RSI_30_70"
    assert state_rsi_bucket(80) == "RSI_70_100"
    assert state_rsi_bucket(120) == "RSI_OUT_OF_RANGE"
    assert state_none() == "NONE"


def test_probability_helpers():
    assert pytest.approx(ConditionalScanner.laplace_smoothing(3, 4), rel=1e-3) == 2/3
    low, high = ConditionalScanner.wilson_score_interval(0.5, 10)
    assert 0 < low < high < 1


def test_best_match_and_pips():
    rows = [
        ConditionalRow("t", "o", "dir", "s", succ=5, tot=10, p=0.5),
        ConditionalRow("t", "o", "dir", "s", succ=8, tot=10, p=0.5),
        ConditionalRow("t", "o", "dir", "s", succ=6, tot=8, p=0.6),
    ]
    best = ConditionalScanner(ScanConfig()).best_match(rows)
    assert best.tot == 8
    assert pips(0.0005, decimals=4) == 5.0


def test_scan_writes_headers(tmp_path: Path):
    scanner = ConditionalScanner(ScanConfig(months_back=1))
    table_path = scanner.scan("EURUSD", tmp_path)
    assert table_path.exists()
    with table_path.open() as fh:
        reader = csv.reader(fh)
        header = next(reader)
    assert header == ["symbol","trigger","outcome","dir","state","succ","tot","p"]
