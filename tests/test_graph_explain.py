from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)
H = lambda u: {"X-User-Id": u}  # noqa: E731

RIPPLE = ["J1", "J6", "K3", "K4", "K7", "K9", "K11", "K13", "K15", "L2", "L4", "L6", "L7"]


def setup_function():
    c.post("/api/demo/reset", headers=H("priya"))


def test_ripple_memory_shape_and_chain():
    r = c.get("/api/graph/ripple?site_id=A&step_code=J1", headers=H("dan")).json()
    assert r["source"] == "memory"
    assert [n["code"] for n in r["path"]] == RIPPLE
    assert r["hops"] == len(RIPPLE) - 1 and r["affected_count"] == 18
    assert "DEPENDS_ON" in r["cypher"] and isinstance(r["ms"], float)


def test_ripple_scoped_to_callers_sites():
    assert c.get("/api/graph/ripple?site_id=C&step_code=K3", headers=H("dan")).status_code == 403
    assert c.get("/api/graph/ripple?site_id=A&step_code=J1", headers=H("marcus")).status_code == 403


def _delay_and_gap():
    p = c.post("/api/ingest/text", headers=H("dan"),
               json={"site_id": "A", "text": "Roofing delayed, heavy rain, about five days."}).json()
    pid = p["proposals"][0]["id"]
    c.post(f"/api/proposals/{pid}/decide", headers=H("priya"), json={"accept": True})
    return c.get("/api/sync-board", headers=H("priya")).json()["gaps"][0]["id"]


def test_swap_explain_anonymised_for_lender_before_link():
    gid = _delay_and_gap()
    r = c.get(f"/api/graph/swap-explain?gap_id={gid}", headers=H("priya")).json()
    assert r["source"] == "memory" and "APPROVED_AT" in r["cypher"] and "point.distance" in r["cypher"]
    row = r["rows"][0]
    assert row["km"] == 1.73 and row["step_code"] is None
    assert row["target_site"].startswith("#") and "Riverside" not in str(r) and "Bow Wharf" not in str(r)


def test_swap_explain_hidden_from_non_party():
    gid = _delay_and_gap()
    assert c.get(f"/api/graph/swap-explain?gap_id={gid}", headers=H("marcus")).status_code == 403
    assert c.get("/api/graph/swap-explain?gap_id=nope", headers=H("priya")).status_code == 404


def test_stats_memory():
    s = c.get("/api/graph/stats", headers=H("priya")).json()
    assert s["source"] == "memory" and s["nodes"] > 400 and s["relationships"] > 800
