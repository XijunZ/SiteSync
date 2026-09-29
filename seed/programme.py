import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent / "development_programme_seed.csv"
ON_SITE = tuple("FGHJKL")
EXTRA_DEPS = {"K3": ["J6"]}  # M&E first fix needs the building weathertight (spec §4)

TRADE_MAP: dict[str, tuple[str, bool]] = {
    "Surveyor": ("surveyor", False), "Council": ("council", False),
    "Utility companies": ("utilities", False), "Milestone": ("milestone", False),
    "Building control": ("building_control", False), "General contractor": ("general_contractor", False),
    "Developer": ("developer", False),
    "Groundworks": ("groundworks", True), "Groundworks, concrete": ("groundworks", True),
    "Concrete": ("concrete", True), "Demolition": ("demolition", True),
    "Demolition, haulage": ("demolition", True), "Licensed asbestos contractor": ("asbestos", True),
    "Specialist contractor": ("ground_investigation", True), "Piling contractor": ("piling", True),
    "RC frame": ("rc_frame", True), "Roofing": ("roofing", True), "Glazing": ("glazing", True),
    "Cladding": ("cladding", True), "Scaffolding": ("scaffolding", True),
    "Bricklaying": ("bricklaying", True), "Mechanical and electrical": ("mep", True),
    "Drylining": ("drylining", True), "Fit-out carpentry": ("carpentry", True),
    "Painting, flooring": ("finishes", True), "Lift contractor": ("lifts", True),
    "Landscaping": ("landscaping", True),
}

HEADCOUNT = {"demolition": 6, "groundworks": 6, "concrete": 5, "piling": 4, "rc_frame": 8,
             "roofing": 4, "glazing": 4, "cladding": 5, "scaffolding": 4, "bricklaying": 5,
             "mep": 6, "drylining": 5, "carpentry": 4, "finishes": 4, "lifts": 3,
             "landscaping": 4, "asbestos": 4, "ground_investigation": 3}


def load_programme(path: Path = CSV_PATH) -> list[dict]:
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["id"].startswith(ON_SITE)]
    ids = {r["id"] for r in rows}
    out = []
    for r in rows:
        raw = r["owner_or_trade"]
        if raw not in TRADE_MAP:
            raise ValueError(f"unknown trade {raw!r} on step {r['id']}")
        trade, has_crew = TRADE_MAP[raw]
        deps = [d for d in r["depends_on"].split(";") if d in ids] + EXTRA_DEPS.get(r["id"], [])
        out.append({
            "code": r["id"], "phase": r["phase"], "name": r["name"], "trade": trade,
            "has_crew": has_crew, "days": int(r["duration_working_days"]), "deps": deps,
            "weather_sensitive": r["weather_sensitive"] == "1", "kind": r["kind"],
            "risk_note": r["delay_risk"] or None,
            "headcount": HEADCOUNT.get(trade, 0) if has_crew else 0,
        })
    return out
