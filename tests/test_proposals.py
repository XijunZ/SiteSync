import pytest
from app.proposals import StaleProposal, build_proposal, decide_proposal
from seed.seed import build_world

SRC = {"kind": "voice", "excerpt": "roofing delayed, heavy rain, about five days"}

def _prop(w):
    return build_proposal(w, w.users["dan"], "A", [{"step_id": "A-J1", "field": "delay_days", "to": 5}], SRC)

def test_knock_on_preview_has_dates_and_labour():
    w = build_world()
    p = _prop(w)
    k = p["knock_on"]
    assert len([m for m in k["moved"] if m["step_id"] != "A-J1"]) == 18
    assert (k["finish_from"], k["finish_to"]) == (397, 402)
    assert [(i["type"], i["step_id"], i["start"], i["end"]) for i in k["labour"]["created"]] == [("SURPLUS", "A-K3", 230, 235)]
    assert p["needs_pm"] is True
    assert w.steps["A-J1"].delay_days == 0  # preview only

def test_site_manager_then_pm_confirm():
    w = build_world()
    p = _prop(w)
    r1 = decide_proposal(w, w.users["dan"], p["id"], True)
    assert r1["status"] == "SITE_CONFIRMED" and w.steps["A-J1"].delay_days == 0
    r2 = decide_proposal(w, w.users["priya"], p["id"], True)
    assert r2["status"] == "APPLIED" and w.steps["A-J1"].delay_days == 5
    assert w.versions["A"] == 1 and w.snapshots[-1]["site_id"] == "A"

def test_stale_or_repeated_decision_rejected():
    w = build_world()
    p = _prop(w)
    decide_proposal(w, w.users["priya"], p["id"], True)
    with pytest.raises(StaleProposal):
        decide_proposal(w, w.users["priya"], p["id"], True)

def test_other_org_cannot_decide():
    w = build_world()
    p = _prop(w)
    with pytest.raises(PermissionError):
        decide_proposal(w, w.users["marcus"], p["id"], True)

def test_invalid_delay_blocked():
    w = build_world()
    with pytest.raises(ValueError):
        build_proposal(w, w.users["dan"], "A", [{"step_id": "A-J1", "field": "delay_days", "to": 90}], SRC)
