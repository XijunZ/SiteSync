from seed.programme import load_programme
from seed.seed import build_world

def test_programme_has_52_on_site_steps_with_k3_j6():
    steps = load_programme()
    assert len(steps) == 52
    k3 = next(s for s in steps if s["code"] == "K3")
    assert "J6" in k3["deps"] and "K1" in k3["deps"]
    assert all(d[0] in "FGHJKL" for s in steps for d in s["deps"])

def test_world_shape():
    w = build_world()
    assert set(w.sites) == {"A", "B", "C", "D"}
    assert len(w.steps) == 4 * 52
    assert w.sites["A"].org_id == "NG" and w.sites["C"].org_id == "RV"
    assert w.steps["A-K3"].headcount == 6
    s1 = [b for b in w.bookings.values() if b.crew_id == "SPARKS-S1"]
    assert any(b.step_id == "A-K3" and (b.start, b.end) == (230, 250) for b in s1)
    s2 = [b for b in w.bookings.values() if b.crew_id == "SPARKS-S2"]
    assert any(b.step_id == "C-K3" and (b.start, b.end) == (225, 245) for b in s2)
    assert any(b.step_id == "A-K5" and b.crew_id.startswith("VOLT") for b in w.bookings.values())
    assert {(a.sub_org_id, a.gc_org_id) for a in w.approvals} >= {("SPARKS", "NG"), ("SPARKS", "RV")}
    assert set(w.users) == {"dan", "priya", "marcus", "sam", "ops"}
