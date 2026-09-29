import json
import pytest
from app.views import city_view, sites_view, sync_board_view, timeline_view
from seed.seed import build_world

FORBIDDEN_FOR_NG = ["Bow Wharf", "Canning Town", "\"C-", "\"D-", "Marcus", "Riverside"]

def _delayed():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    return w

def test_priya_sees_only_own_sites_and_no_leaks():
    w = _delayed()
    p = w.users["priya"]
    blob = json.dumps([sites_view(w, p), sync_board_view(w, p), city_view(w, p), timeline_view(w, p, "A")])
    assert {s["id"] for s in sites_view(w, p)} == {"A", "B"}
    for f in FORBIDDEN_FOR_NG:
        assert f not in blob, f

def test_dan_cannot_open_site_b():
    w = build_world()
    with pytest.raises(PermissionError):
        timeline_view(w, w.users["dan"], "B")

def test_city_view_is_anonymised():
    w = build_world()
    cv = city_view(w, w.users["priya"])
    assert len(cv) == 2
    # Spec v2.1: area, phase and open offers only; trade windows need a shared view.
    assert all({"anon_id", "anon_label", "area", "distance_band", "phase", "offers"} <= set(p) for p in cv)
    assert all("windows" not in p and "trades" not in p for p in cv)

def test_sync_board_shows_gap_and_needs_link():
    w = _delayed()
    board = sync_board_view(w, w.users["priya"])
    g = board["gaps"][0]
    assert g["step_code"] == "K3" and g["warning_days"] == 10
    m8 = next(o for o in g["options"] if o["mechanism"] == "M8")
    assert m8["needs_link"] is True and "target_anon_id" in m8
