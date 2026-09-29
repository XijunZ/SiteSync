from app.domain import Approval, Booking, Crew, Org, Site, Step, User, World
from app.schedule import forward_pass
from seed.programme import load_programme

SITES = [
    ("A", "Hackney Wick Yard", "NG", 51.5433, -0.0243, 12),
    ("B", "Stratford Mill", "NG", 51.5417, -0.0036, 100),
    ("C", "Bow Wharf", "RV", 51.5282, -0.0183, 7),
    ("D", "Canning Town Works", "RV", 51.5147, 0.0080, 185),
]
DAY_VALUE = 8000  # £ per site per day of delay (demo assumption, shown on screen)
SPARKS_CREW_BY_SITE = {"A": "SPARKS-S1", "C": "SPARKS-S2"}


def build_world() -> World:
    w = World()
    for org in [Org("NG", "Northgate Build", "GC"), Org("RV", "Riverside Construction", "GC"),
                Org("SPARKS", "Sparks Electrical", "SUB"), Org("VOLT", "Voltline M&E", "SUB"),
                Org("CREWNOW", "CrewNow Agency", "AGENCY")]:
        w.orgs[org.id] = org
    for u in [User("dan", "Dan", "SITE_MANAGER", "NG", ["A"]), User("priya", "Priya", "PM", "NG", ["A", "B"]),
              User("marcus", "Marcus", "PM", "RV", ["C", "D"]), User("sam", "Sam", "SUB_PLANNER", "SPARKS", []),
              User("ops", "SiteSync operator", "OPERATOR", "SITESYNC", [])]:
        w.users[u.id] = u
    templates = load_programme()
    for sid, name, org, lat, lon, off in SITES:
        w.sites[sid] = Site(sid, name, org, lat, lon, off, DAY_VALUE, area="East London")
        w.versions[sid] = 0
        for t in templates:
            w.steps[f"{sid}-{t['code']}"] = Step(
                id=f"{sid}-{t['code']}", site_id=sid, code=t["code"], phase=t["phase"], name=t["name"],
                trade=t["trade"], has_crew=t["has_crew"], kind=t["kind"], days=t["days"],
                deps=[f"{sid}-{d}" for d in t["deps"]], weather_sensitive=t["weather_sensitive"],
                risk_note=t["risk_note"], headcount=t["headcount"])
    for cid, name in [("SPARKS-S1", "Sparks crew 1"), ("SPARKS-S2", "Sparks crew 2")]:
        w.crews[cid] = Crew(cid, "SPARKS", "mep", 6, name)
    w.approvals += [Approval("SPARKS", "NG"), Approval("SPARKS", "RV"), Approval("VOLT", "NG"),
                    Approval("VOLT", "RV"), Approval("CREWNOW", "NG", setup_days=1),
                    Approval("CREWNOW", "RV", setup_days=1)]
    # Bow Wharf's lower-floor first fix is a large floor plate: two crews' worth of M&E (12), only one booked.
    w.steps["C-K3"].headcount = 12
    for sid in w.sites:
        base = forward_pass(w, sid, "baseline")
        for st in [s for s in w.steps.values() if s.site_id == sid and s.has_crew and s.headcount]:
            crew_id = _crew_for(w, st)
            start, end = base[st.id]
            bid = w.next_id("bk")
            w.bookings[bid] = Booking(bid, crew_id, st.id, start, end)
    return w


def _crew_for(w: World, st: Step) -> str:
    if st.trade == "mep":
        if st.code != "K5" and st.site_id in SPARKS_CREW_BY_SITE:
            return SPARKS_CREW_BY_SITE[st.site_id]
        cid = f"VOLT-{st.site_id}"
        w.crews.setdefault(cid, Crew(cid, "VOLT", "mep", 6, f"Voltline crew {st.site_id}"))
        return cid
    gc = w.sites[st.site_id].org_id
    cid = f"{gc}-{st.trade}-{st.site_id}"  # one direct crew per trade per site
    w.crews.setdefault(cid, Crew(cid, gc, st.trade, st.headcount, f"{w.orgs[gc].name} {st.trade} ({st.site_id})"))
    return cid
