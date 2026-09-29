"""Write API responses for each demo user at key steps of the PRD §7 story to tests/fixtures/,
so the UI can be built and checked against real shapes."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("LLM_PROVIDERS", "")
os.environ["STORE"] = "memory"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app import ingest  # noqa: E402
from app.main import app  # noqa: E402

ingest._llm_extract = lambda *a, **k: None  # deterministic, offline
c = TestClient(app)
out = Path("tests/fixtures")
out.mkdir(parents=True, exist_ok=True)
for f in out.glob("*.json"):
    f.unlink()


def H(u):
    return {"X-User-Id": u}


def get(u, p):
    r = c.get(p, headers=H(u))
    return r.json() if r.status_code == 200 else {"status": r.status_code, **r.json()}


def dump(tag: str) -> None:
    for user in ("dan", "priya", "marcus", "sam"):
        data = {p: get(user, p) for p in ("/api/me", "/api/sites", "/api/sync-board", "/api/city", "/api/offers",
                                          "/api/requests", "/api/notifications", "/api/links", "/api/report",
                                          "/api/events")}
        for s in data["/api/sites"] if isinstance(data["/api/sites"], list) else []:
            for suffix in ("timeline", "labour", "trades"):
                data[f"/api/sites/{s['id']}/{suffix}"] = get(user, f"/api/sites/{s['id']}/{suffix}")
            data[f"/api/proposals?site_id={s['id']}"] = get(user, f"/api/proposals?site_id={s['id']}")
        for o in data["/api/offers"] if isinstance(data["/api/offers"], list) else []:
            if not o.get("own"):
                data[f"/api/city/{o['anon_id']}/overlay"] = get(user, f"/api/city/{o['anon_id']}/overlay")
        if user == "sam":
            data["/api/sub/bookings"] = get(user, "/api/sub/bookings")
        (out / f"{tag}_{user}.json").write_text(json.dumps(data, indent=2))


def post(u, p, b=None):
    return c.post(p, headers=H(u), json=b or {}).json()


post("priya", "/api/demo/reset")
dump("01_seed")
preview = post("dan", "/api/proposals/preview", {"site_id": "A", "step_id": "A-J1", "finish": 235})
(out / "01_preview_dan.json").write_text(json.dumps(preview, indent=2))
pid = post("dan", "/api/ingest/text", {"site_id": "A", "text": "Roofing delayed, heavy rain, about five days."})[
    "proposals"][0]["id"]
dump("02_proposed")
post("dan", f"/api/proposals/{pid}/decide", {"accept": True})
dump("03_site_confirmed")
post("priya", f"/api/proposals/{pid}/decide", {"accept": True})
dump("04_approved")
gap = get("priya", "/api/sync-board")["gaps"][0]
offer = post("priya", "/api/offers", {"gap_id": gap["id"]})
dump("05_offered")
anon = get("marcus", "/api/offers")[0]["anon_id"]
vr = post("marcus", "/api/view-requests", {"anon_id": anon})
dump("06_view_requested")
post("priya", f"/api/view-requests/{vr['id']}/decide", {"share": True})
dump("07_view_shared")
link = post("marcus", "/api/links", {"offer_id": offer["id"], "purpose": "Pool M&E capacity"})
dump("08_crew_requested")
post("priya", f"/api/links/{link['id']}/decide", {"accept": True, "pool_terms": {"trades": ["mep"]}})
dump("09_accepted")
prop = next(i for i in get("sam", "/api/requests")["incoming"] if i["kind"] == "proposal")
post("sam", f"/api/cross-proposals/{prop['id']}/decide", {"accept": True})
dump("10_sub_accepted")
mb = next(i for i in get("marcus", "/api/requests")["incoming"] if i["kind"] == "booking")
post("marcus", mb["actions"][0]["path"], mb["actions"][0]["body"])
dump("11_borrower_confirmed")
pb = next(i for i in get("priya", "/api/requests")["incoming"] if i["kind"] == "booking")
post("priya", pb["actions"][0]["path"], pb["actions"][0]["body"])
dump("12_done")
post("priya", "/api/demo/reset")
print("fixtures written to", out, "-", len(list(out.glob("*.json"))), "files")
