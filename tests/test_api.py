from fastapi.testclient import TestClient
from app import ingest
from app.main import app

c = TestClient(app)
H = lambda u: {"X-User-Id": u}

def setup_function():
    c.post("/api/demo/reset", headers=H("priya"))

def test_unknown_user_401():
    assert c.get("/api/sites").status_code == 401
    assert c.get("/api/sites", headers=H("nobody")).json()["error"] == "unknown_user"

def test_chatter_gives_no_proposal(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    r = c.post("/api/ingest/text", headers=H("dan"), json={"site_id": "A", "text": "All good today."}).json()
    assert r["proposals"] == [] and "No schedule change" in r["message"]

def test_demo_story_end_to_end(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    p = c.post("/api/ingest/text", headers=H("dan"), json={"site_id": "A",
               "text": "Roofing delayed, heavy rain, about five days."}).json()
    pid = p["proposals"][0]["id"]
    assert c.post(f"/api/proposals/{pid}/decide", headers=H("dan"), json={"accept": True}).json()["status"] == "SITE_CONFIRMED"
    assert c.post(f"/api/proposals/{pid}/decide", headers=H("priya"), json={"accept": True}).json()["status"] == "APPLIED"
    r = c.post(f"/api/proposals/{pid}/decide", headers=H("priya"), json={"accept": True})
    assert r.status_code == 409 and r.json()["error"] == "stale"
    board = c.get("/api/sync-board", headers=H("priya")).json()
    gap = board["gaps"][0]
    anon = next(o for o in gap["options"] if o["mechanism"] == "M8")["target_anon_id"]
    link = c.post("/api/links", headers=H("priya"), json={"anon_id": anon, "purpose": "pool M&E"}).json()
    c.post(f"/api/links/{link['id']}/decide", headers=H("marcus"), json={"accept": True, "pool_terms": {"trades": ["mep"]}})
    r = c.post("/api/options/approve", headers=H("priya"), json={"gap_id": gap["id"], "mechanism": "M8"}).json()
    cp = r["cross_proposal_id"]
    c.post(f"/api/cross-proposals/{cp}/decide", headers=H("marcus"), json={"accept": True})
    c.post(f"/api/cross-proposals/{cp}/decide", headers=H("sam"), json={"accept": True})
    for user, site in (("marcus", "C"), ("priya", "A")):
        for prop in c.get(f"/api/proposals?site_id={site}", headers=H(user)).json():
            c.post(f"/api/proposals/{prop['id']}/decide", headers=H(user), json={"accept": True})
    final = c.get("/api/sync-board", headers=H("priya")).json()
    assert final["gaps"] == [] and final["days_protected"] == 3

def test_reset_clears_everything():
    anon = c.get("/api/city", headers=H("priya")).json()[0]["anon_id"]
    c.post("/api/links", headers=H("priya"), json={"anon_id": anon, "purpose": "x"})
    c.post("/api/demo/reset", headers=H("priya"))
    assert c.get("/api/links", headers=H("priya")).json() == []
    assert c.get("/api/events", headers=H("priya")).json() == []
