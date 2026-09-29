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
    """Spec §10 test_link_flow: offer → crew request → accept (M8 + sub proposal) → confirms."""
    w, priya, marcus, sam = _delayed()
    gap = [g for g in open_gaps(w) if g.type == "SURPLUS"][0]
    offer = publish_offer(w, priya, gap.id)
    assert offer.status == "OPEN"
    assert not view_granted(w, "A", "RV")  # no view grant needed to request the offered crew
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
    assert [g for g in open_gaps(w) if g.type == "SURPLUS"] == []
    assert w.outcomes[-1]["days_protected"] == 3 and w.outcomes[-1]["value_gbp"] == 24000


def test_decline_reopens_offer():
    w, priya, marcus, _ = _delayed()
    offer = publish_offer(w, priya, [g for g in open_gaps(w) if g.type == "SURPLUS"][0].id)
    link = request_link(w, marcus, offer.id, "x")
    decide_link(w, priya, link.id, False)
    assert link.status == "DECLINED" and offer.status == "OPEN"


def test_cannot_request_own_offer_or_view_own_site():
    w, priya, _, _ = _delayed()
    offer = publish_offer(w, priya, [g for g in open_gaps(w) if g.type == "SURPLUS"][0].id)
    with pytest.raises(ValueError):
        request_link(w, priya, offer.id, "x")
    with pytest.raises(ValueError):
        request_view(w, priya, anon_id("B"))


def test_marcus_posts_need_then_priya_offer_matches_it():
    import json
    from app.network import post_need
    from app.views import sync_board_view, requests_view, offers_view
    w = build_world()
    marcus, priya = w.users["marcus"], w.users["priya"]
    short = [g for g in open_gaps(w) if g.type == "SHORTAGE"][0]
    assert (short.step_id, short.workers) == ("C-K3", 6)
    opts = {o["mechanism"] for o in sync_board_view(w, marcus)["gaps"][0]["options"]}
    assert {"M13", "M10"} <= opts
    nd = post_need(w, marcus, short.id)
    assert (nd.start, nd.end, nd.workers) == (225, 245, 6)
    w.steps["A-J1"].delay_days = 5
    board = sync_board_view(w, priya)
    m8 = next(o for o in board["gaps"][0]["options"] if o["mechanism"] == "M8")
    assert m8["matching_need"]["workers"] == 6
    # anonymity: Priya sees Riverside's need without names
    blob = json.dumps(board)
    for f in ("Bow Wharf", "Riverside", "Marcus", "C-K3"):
        assert f not in blob, f
    sur = [g for g in open_gaps(w) if g.type == "SURPLUS"][0]
    offer = publish_offer(w, priya, sur.id)
    assert offer.need_id == nd.id and w.needs[nd.id].status == "MATCHED"
    mo = offers_view(w, marcus)
    assert mo[0]["matches_your_request"] and mo[0]["notice_days"] == 10
    assert requests_view(w, marcus)["outgoing"][0]["kind"] == "need"
    assert "matched" in w.notifications[-1]["text"].lower() or any("matched" in n["text"].lower() for n in w.notifications)
