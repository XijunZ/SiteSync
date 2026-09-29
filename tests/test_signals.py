from app.schedule import forward_pass, site_finish
from app.signals import clear_risk, raise_risk, wet_days
from seed.seed import build_world

def test_risk_moves_risk_forecast_not_confirmed():
    w = build_world()
    r = raise_risk(w, "A", "J1", 2, "weather", "Rain Thu–Fri")
    assert r["risk_finish"] == 399 and r["confirmed_finish"] == 397
    assert "J1" in r["question"]
    assert site_finish(forward_pass(w, "A", "confirmed")) == 397
    clear_risk(w, "A", "J1")
    assert site_finish(forward_pass(w, "A", "risk")) == 397

def test_wet_days():
    assert wet_days([0.0, 5.1, 3.0, 0.4]) == [1, 2]
