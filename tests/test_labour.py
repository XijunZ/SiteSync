from app.domain import Booking
from app.labour import diff_imbalances, imbalances
from app.schedule import all_dates
from seed.seed import build_world

def test_no_imbalances_in_lookahead_at_seed():
    w = build_world()
    assert imbalances(w, all_dates(w)) == []

def test_roof_delay_creates_exactly_one_mep_surplus():
    w = build_world()
    before = imbalances(w, all_dates(w))
    w.steps["A-J1"].delay_days = 5
    after = imbalances(w, all_dates(w))
    assert len(after) == 1
    i = after[0]
    assert (i.type, i.site_id, i.step_id, i.crew_id, i.trade, i.start, i.end, i.workers) == \
        ("SURPLUS", "A", "A-K3", "SPARKS-S1", "mep", 230, 235, 6)
    d = diff_imbalances(before, after)
    assert d["created"] == after and d["resolved"] == []

def test_booking_elsewhere_makes_crew_days_productive():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    w.bookings["x"] = Booking("x", "SPARKS-S1", "C-K3", 230, 235, source="swap")
    assert imbalances(w, all_dates(w)) == []

def test_clash_when_same_crew_needed_twice():
    w = build_world()
    w.bookings["y"] = Booking("y", "SPARKS-S1", "C-K3", 230, 235, source="test")
    types = {i.type for i in imbalances(w, all_dates(w))}
    assert "CLASH" in types
