import json

from fastapi.testclient import TestClient
from app import ingest, plaud
from app.main import app

c = TestClient(app)
H = lambda u: {"X-User-Id": u}


def setup_function():
    c.post("/api/demo/reset", headers=H("priya"))


def post(user, path, body=None):
    return c.post(path, headers=H(user), json=body or {})


def get(user, path):
    return c.get(path, headers=H(user))


def test_unknown_user_401():
    assert c.get("/api/sites").status_code == 401
    assert c.get("/api/sites", headers=H("nobody")).json()["error"] == "unknown_user"


def test_chatter_gives_no_proposal(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    r = post("dan", "/api/ingest/text", {"site_id": "A", "text": "All good today."}).json()
    assert r["proposals"] == [] and "No schedule change" in r["message"]


def test_demo_opens_with_supplier_signal_and_no_impact_clears_it():
    t = get("dan", "/api/sites/A/timeline").json()
    assert [r["step_code"] for r in t["risk_signals"]] == ["J1"]
    assert "batch 2" in t["risk_signals"][0]["detail"] and "failed factory QA" in t["risk_signals"][0]["detail"]
    site = get("priya", "/api/sites").json()[0]
    assert (site["confirmed_finish"], site["risk_finish"]) == (397, 402)
    r = post("dan", "/api/signals/clear", {"site_id": "A", "step_code": "J1"}).json()
    assert r["risk_finish"] == 397
    assert get("dan", "/api/sites/A/timeline").json()["risk_signals"] == []


def test_timeline_edit_preview_and_validation():
    ok = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "finish": 235}).json()
    assert ok["error"] is None and ok["moved_count"] == 18
    assert (ok["finish_from"], ok["finish_to"], ok["new_gaps_in_lookahead"]) == (397, 402, 1)
    assert any(g["type"] == "EXTEND" for g in ok["labour"]["created"])
    bad = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "start": 230, "finish": 225}).json()
    assert "Finish can't be before start" in bad["error"]
    early = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "start": 210}).json()
    assert "predecessors" in early["error"]
    same = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "finish": 230}).json()
    assert "No change" in same["error"]


def test_timeline_start_shift_uses_lag():
    p = post("dan", "/api/proposals", {"site_id": "A", "step_id": "A-J1", "start": 222, "finish": 232,
                                       "reason": "Weather"}).json()
    assert [c["field"] for c in p["changes"]] == ["lag_days"]
    post("priya", f"/api/proposals/{p['id']}/decide", {"accept": True})
    j1 = next(s for s in get("priya", "/api/sites/A/timeline").json()["steps"] if s["code"] == "J1")
    assert j1["confirmed"] == [222, 232]


def test_plaud_routes_shape(monkeypatch):
    monkeypatch.setattr(plaud, "_run", lambda args: (
        "0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b  Morning briefing  2026-09-29 07:42\n" if args[0] == "recent" else
        "[00:00 - 00:04] Dan: Morning all.\n[00:04 - 00:09] Kev: Roof waterproofing delayed about five working days."))
    r = get("dan", "/api/plaud/recordings").json()
    assert r["recordings"][0]["id"] == "0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b"
    t = get("dan", "/api/plaud/recordings/0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b/transcript").json()
    assert t["speakers"] == ["Dan", "Kev"] and "five working days" in t["text"]


def test_plaud_error_is_502(monkeypatch):
    def boom(args):
        raise plaud.PlaudError("Plaud login expired: run `plaud login`")
    monkeypatch.setattr(plaud, "_run", boom)
    r = get("dan", "/api/plaud/recordings")
    assert r.status_code == 502 and r.json()["error"] == "plaud"


def _delay_j1(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    p = post("dan", "/api/ingest/text", {"site_id": "A", "text": "Roofing delayed, heavy rain, about five days."}).json()
    pid = p["proposals"][0]["id"]
    assert post("dan", f"/api/proposals/{pid}/decide", {"accept": True}).json()["status"] == "SITE_CONFIRMED"
    assert post("priya", f"/api/proposals/{pid}/decide", {"accept": True}).json()["status"] == "APPLIED"
    return pid


def test_demo_story_end_to_end(monkeypatch):
    """PRD §7: the 9 clicks (offer → overlay → request crew → accept → confirms)."""
    pid = _delay_j1(monkeypatch)                                                     # 1–3
    r = post("priya", f"/api/proposals/{pid}/decide", {"accept": True})
    assert r.status_code == 409 and r.json()["error"] == "stale"
    assert get("dan", "/api/sites/A/timeline").json()["risk_signals"] == []          # fact supersedes the signal
    gap = get("priya", "/api/sync-board").json()["gaps"][0]
    m8 = next(o for o in gap["options"] if o["mechanism"] == "M8")
    assert m8["feasible"] and m8["offer_state"] == "none"
    offer = post("priya", "/api/offers", {"gap_id": gap["id"]}).json()               # 4
    assert offer["status"] == "OPEN"
    seen = get("marcus", "/api/offers").json()                                        # 5
    assert len(seen) == 1 and seen[0]["fits"]["step_code"] == "K3"
    assert (seen[0]["workers"], seen[0]["start"], seen[0]["end"]) == (6, 230, 235)
    assert any("M&E crew available near you" in n["text"] for n in get("marcus", "/api/notifications").json())
    mine = get("marcus", "/api/sites/C/trades").json()                               # 5: overlay = own windows + offer
    assert "mep" in mine["trades"]
    link = post("marcus", "/api/links", {"offer_id": offer["id"], "purpose": "Pool M&E capacity"}).json()
    crew_req = next(i for i in get("priya", "/api/requests").json()["incoming"] if i["kind"] == "crew")
    assert crew_req["tracker"][1]["state"] == "wait"
    post("priya", f"/api/links/{link['id']}/decide",                                   # 8
         {"accept": True, "pool_terms": {"trades": ["mep"], "return_guarantee": "Back by day 235"}})
    assert get("marcus", "/api/offers").json()[0]["counterparty"] == "Northgate Build"
    assert get("priya", "/api/sync-board").json()["gaps"][0]["options"][0]["offer_state"] == "agreed"
    prop = next(i for i in get("sam", "/api/requests").json()["incoming"] if i["kind"] == "proposal")
    post("sam", f"/api/cross-proposals/{prop['id']}/decide", {"accept": True})         # 9
    mb = next(i for i in get("marcus", "/api/requests").json()["incoming"] if i["kind"] == "booking")
    post("marcus", mb["actions"][0]["path"], mb["actions"][0]["body"])                 # 10
    pb = next(i for i in get("priya", "/api/requests").json()["incoming"] if i["kind"] == "booking")
    post("priya", pb["actions"][0]["path"], pb["actions"][0]["body"])                  # 11
    final = get("priya", "/api/sync-board").json()
    assert final["gaps"] == [] and final["days_protected"] == 3 and final["value_protected_gbp"] == 24000
    rep = get("priya", "/api/report").json()
    assert rep["days_protected"] == 3 and rep["value_gbp"] == 24000 and rep["idle_crew_days_used"] == 5
    assert (rep["rows"][0]["no_action_finish"], rep["rows"][0]["outcome_finish"]) == (405, 402)
    tracker = next(i for i in get("marcus", "/api/requests").json()["outgoing"] if i["kind"] == "crew")["tracker"]
    assert all(s["state"] == "done" for s in tracker)
    sam = get("sam", "/api/sub/bookings").json()
    s1 = [b for b in sam if b["crew_id"] == "SPARKS-S1"]
    assert all(b["idle"] == [] for b in s1 if b["step_code"] == "K3")


def test_anonymity_handoffs(monkeypatch):
    """Spec §10: before Northgate accepts, nothing Riverside sees names Northgate, its sites, codes or people."""
    _delay_j1(monkeypatch)
    gap = get("priya", "/api/sync-board").json()["gaps"][0]
    offer = post("priya", "/api/offers", {"gap_id": gap["id"]}).json()
    anon = get("marcus", "/api/offers").json()[0]["anon_id"]
    assert get("marcus", f"/api/city/{anon}/overlay").status_code == 403   # lender's windows stay private
    post("marcus", "/api/links", {"offer_id": offer["id"], "purpose": "Pool M&E capacity"})
    blob = json.dumps([get("marcus", p).json() for p in (
        "/api/offers", "/api/requests", "/api/notifications", "/api/city", "/api/sync-board", "/api/events",
        "/api/sites", "/api/links", "/api/cross-proposals")])
    for forbidden in ("Northgate", "Hackney Wick", "Stratford", '"A-', '"B-', "Priya", "Dan"):
        assert forbidden not in blob, forbidden


def test_reset_clears_everything(monkeypatch):
    _delay_j1(monkeypatch)
    gap = get("priya", "/api/sync-board").json()["gaps"][0]
    post("priya", "/api/offers", {"gap_id": gap["id"]})
    post("priya", "/api/demo/reset")
    assert get("priya", "/api/links").json() == [] and get("marcus", "/api/offers").json() == []
    assert get("marcus", "/api/notifications").json() == []
    assert [e["type"] for e in get("priya", "/api/events").json()] == ["RiskFlagRaised"]
    assert get("marcus", "/api/events").json() == []


def test_pause_window_edit_and_ingest(monkeypatch):
    pv = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "pause_start": 225, "pause_days": 5}).json()
    assert pv["error"] is None and pv["moved_count"] == 18 and (pv["finish_from"], pv["finish_to"]) == (397, 402)
    bad = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "pause_start": 250, "pause_days": 5}).json()
    assert "within the step" in bad["error"]
    from app import ingest
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    r = post("dan", "/api/ingest/text", {"site_id": "A", "text": "Apex rang: the roof membrane batch failed their quality "
             "check, replacement's due in five working days, so roof waterproofing is on hold until then."}).json()
    p = r["proposals"][0]
    assert {c["field"]: c["to"] for c in p["changes"]}["pause_start"] == 225
    post("dan", f"/api/proposals/{p['id']}/decide", {"accept": True})
    post("priya", f"/api/proposals/{p['id']}/decide", {"accept": True})
    j1 = next(s for s in get("dan", "/api/sites/A/timeline").json()["steps"] if s["code"] == "J1")
    assert j1["pause"]["start"] == 225 and j1["pause"]["end"] == 230 and j1["confirmed"] == [220, 235]
