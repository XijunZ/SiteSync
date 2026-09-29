import pytest
from app.network import (anon_id, decide_cross_proposal, decide_link, decide_view, publish_offer, request_link,
                         request_view, view_granted)
from app.proposals import decide_proposal
from app.sync_engine import open_gaps
from seed.seed import build_world


def _delayed():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    return w, w.users["priya"], w.users["marcus"], w.users["sam"]


def test_link_flow_borrower_asks_lender_decides():
    """Spec §10 test_link_flow: offer → view → share → crew request → accept (M8 + sub proposal) → confirms."""
    w, priya, marcus, sam = _delayed()
    gap = open_gaps(w)[0]
    offer = publish_offer(w, priya, gap.id)
    assert offer.status == "OPEN"
    g = request_view(w, marcus, anon_id("A"))
    assert not view_granted(w, "A", "RV")
    decide_view(w, priya, g.id, True)
    assert view_granted(w, "A", "RV")
    link = request_link(w, marcus, offer.id, "pool M&E")
    assert link.org_a == "RV" and link.org_b == "NG" and link.target_step_id == "C-K3" and offer.status == "REQUESTED"
    with pytest.raises(PermissionError):
        decide_link(w, marcus, link.id, True)
    decide_link(w, priya, link.id, True, {"trades": ["mep"]})
    assert link.status == "ACTIVE" and offer.status == "TAKEN"
    cp = next(iter(w.cross_proposals.values()))
    assert cp["target_step_id"] == "C-K3" and cp["accepted"] == {"RV": True}
    out = decide_cross_proposal(w, sam, cp["id"], True)
    assert out["status"] == "AGREED" and {p["org_id"] for p in out["proposals"]} == {"NG", "RV"}
    rv = next(p for p in out["proposals"] if p["org_id"] == "RV")
    ng = next(p for p in out["proposals"] if p["org_id"] == "NG")
    decide_proposal(w, marcus, rv["id"], True)
    decide_proposal(w, priya, ng["id"], True)
    assert open_gaps(w) == []
    assert w.outcomes[-1]["days_protected"] == 3 and w.outcomes[-1]["value_gbp"] == 24000


def test_decline_reopens_offer():
    w, priya, marcus, _ = _delayed()
    offer = publish_offer(w, priya, open_gaps(w)[0].id)
    link = request_link(w, marcus, offer.id, "x")
    decide_link(w, priya, link.id, False)
    assert link.status == "DECLINED" and offer.status == "OPEN"


def test_cannot_request_own_offer_or_view_own_site():
    w, priya, _, _ = _delayed()
    offer = publish_offer(w, priya, open_gaps(w)[0].id)
    with pytest.raises(ValueError):
        request_link(w, priya, offer.id, "x")
    with pytest.raises(ValueError):
        request_view(w, priya, anon_id("B"))
