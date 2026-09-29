"""Write API responses for each demo user to tests/fixtures/ so the UI can be built against them."""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("LLM_PROVIDERS", "")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

c = TestClient(app)
out = Path("tests/fixtures")
out.mkdir(parents=True, exist_ok=True)


def dump(tag: str) -> None:
    for user in ("dan", "priya", "marcus", "sam"):
        h = {"X-User-Id": user}
        data = {"me": c.get("/api/me", headers=h).json(), "sites": c.get("/api/sites", headers=h).json(),
                "sync_board": c.get("/api/sync-board", headers=h).json(), "city": c.get("/api/city", headers=h).json(),
                "links": c.get("/api/links", headers=h).json(), "cross": c.get("/api/cross-proposals", headers=h).json()}
        if data["sites"]:
            sid = data["sites"][0]["id"]
            data["timeline"] = c.get(f"/api/sites/{sid}/timeline", headers=h).json()
            data["labour"] = c.get(f"/api/sites/{sid}/labour", headers=h).json()
            data["proposals"] = c.get(f"/api/proposals?site_id={sid}", headers=h).json()
        (out / f"{user}_{tag}.json").write_text(json.dumps(data, indent=2))


c.post("/api/demo/reset")
dump("seed")
r = c.post("/api/ingest/text", headers={"X-User-Id": "dan"},
           json={"site_id": "A", "text": "Roofing delayed, heavy rain, about five days."}).json()
dump("proposed")
pid = r["proposals"][0]["id"]
c.post(f"/api/proposals/{pid}/decide", headers={"X-User-Id": "priya"}, json={"accept": True})
dump("delayed")
c.post("/api/demo/reset")
print("fixtures written to", out)
