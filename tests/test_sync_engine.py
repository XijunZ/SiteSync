from app.domain import Link
from app.sync_engine import open_gaps, options_for
from seed.seed import build_world

def _delayed():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    return w

def test_one_gap_with_warning_days():
    gaps = [g for g in open_gaps(_delayed()) if g.site_id == "A"]
    assert len(gaps) == 1
    g = gaps[0]
    assert (g.type, g.step_id, g.start, g.end, g.warning_days) == ("SURPLUS", "A-K3", 230, 235, 10)

def test_options_before_link():
    w = _delayed()
    opts = {o.mechanism: o for o in options_for(w, [g for g in open_gaps(w) if g.type == "SURPLUS"][0])}
    assert not opts["M1"].feasible and "K5" in opts["M1"].reason
    assert opts["M3"].feasible and opts["M3"].days_protected == 3 and opts["M3"].start_by == 230
    m8 = opts["M8"]
    # Offering the idle days needs no link (spec §5.7); the link still gates the swap itself.
    assert m8.feasible and m8.needs_link_with == "RV"
    assert m8.target_step_id == "C-K3" and round(m8.distance_km, 1) == 1.7
    assert m8.days_protected == 3 and m8.idle_cost_avoided_gbp == 6000 and m8.start_by == 229

def test_m8_feasible_and_ranked_first_after_link():
    w = _delayed()
    w.links["L1"] = Link("L1", "NG", "RV", "priya", "pool M&E", status="ACTIVE")
    ranked = options_for(w, [g for g in open_gaps(w) if g.type == "SURPLUS"][0])
    assert ranked[0].mechanism == "M8" and ranked[0].feasible
    assert ranked[0].value_gbp == 3 * 8000 + 6000


def test_m8_approve_without_link_is_refused():
    import pytest
    from app.sync_engine import approve_option
    w = _delayed()
    with pytest.raises(ValueError, match="Offer the idle days first"):
        approve_option(w, w.users["priya"], [g for g in open_gaps(w) if g.type == "SURPLUS"][0].id, "M8")
