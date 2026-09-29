from app.schedule import all_dates, critical_steps, forward_pass, site_finish
from seed.seed import build_world

def test_baseline_stages_on_day_220():
    w = build_world()
    d = all_dates(w, "baseline")
    assert d["A"]["A-J1"] == (220, 230)
    assert d["B"]["B-G5"][0] == 220
    assert d["C"]["C-K3"] == (225, 245)
    assert d["D"]["D-F7"][0] == 220
    assert site_finish(d["A"]) == 397

def test_j1_plus_5_moves_18_steps_and_finish():
    w = build_world()
    before = forward_pass(w, "A", "confirmed")
    w.steps["A-J1"].delay_days = 5
    after = forward_pass(w, "A", "confirmed")
    moved = {k for k in before if after[k] != before[k] and k != "A-J1"}
    assert len(moved) == 18
    assert all(after[k][0] - before[k][0] == 5 for k in moved)
    assert site_finish(after) == 402
    assert after["A-K3"] == (235, 255)

def test_min_start_models_late_crew_return():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    late = forward_pass(w, "A", "confirmed", min_start={"A-K3": 238})
    assert site_finish(late) == 405

def test_risk_mode_adds_risk_days_only_in_risk_mode():
    w = build_world()
    w.steps["A-J1"].risk_days = 2
    assert site_finish(forward_pass(w, "A", "confirmed")) == 397
    assert forward_pass(w, "A", "risk")["A-J1"] == (220, 232)

def test_k3_is_critical_after_delay():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    d = forward_pass(w, "A", "confirmed")
    assert "A-K3" in critical_steps(w, "A", d)
