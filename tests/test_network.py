import pytest
from app.network import anon_id, decide_cross_proposal, decide_link, request_link
from app.sync_engine import approve_option, open_gaps
from seed.seed import build_world

def test_full_link_and_swap_flow():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    priya, marcus, sam = w.users["priya"], w.users["marcus"], w.users["sam"]
    link = request_link(w, priya, anon_id("C"), "pool M&E capacity")
    assert link.status == "REQUESTED" and link.org_b == "RV"
    with pytest.raises(PermissionError):
        decide_link(w, priya, link.id, True)
    decide_link(w, marcus, link.id, True, {"trades": ["mep"], "return_guarantee": True})
    assert w.links[link.id].status == "ACTIVE"
    gap = open_gaps(w)[0]
    res = approve_option(w, priya, gap.id, "M8")
    cp_id = res["cross_proposal_id"]
    decide_cross_proposal(w, marcus, cp_id, True)
    out = decide_cross_proposal(w, sam, cp_id, True)
    assert out["status"] == "AGREED"
    assert {p["org_id"] for p in out["proposals"]} == {"NG", "RV"}

def test_request_link_to_own_org_rejected():
    w = build_world()
    with pytest.raises(ValueError):
        request_link(w, w.users["priya"], anon_id("B"), "x")
