import os, json, tempfile
from .indicator_status import IndicatorStatus, format_indicator_key
from .indicator_parameter_generator import generate_percent_change_param_sets
from .dynamic_matrix_manager import DynamicMatrixManager

def test_format_key():
    assert format_indicator_key(IndicatorStatus.TEST, "rsi divergence") == "TEST_RSI_DIVERGENCE"

def test_generate_params_respects_cap():
    # Intentionally set base risk above cap
    sets = generate_percent_change_param_sets([15, 60], base_risk=9.99)
    assert all(s['global_risk_percent'] <= 3.5 for s in sets)
    assert sets[0]['window_minutes'] == 15 and sets[1]['window_minutes'] == 60

def test_register_indicator_adds_context_and_clamps(tmp_path=None):
    tmp = os.path.join(tempfile.gettempdir(), "matrix_test.json")
    if os.path.exists(tmp):
        os.remove(tmp)
    mgr = DynamicMatrixManager(storage_path=tmp)
    params = dict(global_risk_percent=9.99, bias="BOTH")
    out = mgr.register_indicator(
        name="percent_change", status=IndicatorStatus.EXPERIMENTAL,
        symbols=["EURUSD"], base_params=params, windows=[15, 60]
    )
    assert len(out) == 2
    for c in out:
        assert c["indicator_key"].startswith("EXP_")
        assert c["context"] in {"CTX:W15", "CTX:W60"}
        assert c["params"]["global_risk_percent"] == 3.5  # clamped
