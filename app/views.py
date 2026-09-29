from collections import defaultdict
from dataclasses import asdict

from app.config import CREW_DAY_GBP, TODAY
from app.domain import User, World
from app.labour import imbalances
from app.network import anon_id
from app.schedule import all_dates, critical_steps, forward_pass, site_finish
from app.sync_engine import distance_km, link_active, open_gaps, options_for


def visible_sites(world: World, user: User) -> list[str]:
    if user.role in ("PM", "OPS_DIRECTOR"):
        return [s for s, site in world.sites.items() if site.org_id == user.org_id]
    if user.role == "SITE_MANAGER":
        return list(user.site_ids)
    return []


def check_site(world: World, user: User, site_id: str) -> None:
    if site_id not in visible_sites(world, user):
        raise PermissionError("site not in your scope")


def sites_view(world: World, user: User) -> list[dict]:
    out = []
    for sid in visible_sites(world, user):
        s = world.sites[sid]
        base = site_finish(forward_pass(world, sid, "baseline"))
        conf = site_finish(forward_pass(world, sid, "confirmed"))
        risk = site_finish(forward_pass(world, sid, "risk"))
        out.append({"id": sid, "name": s.name, "start": s.offset, "baseline_finish": base,
                    "confirmed_finish": conf, "risk_finish": risk, "variance": conf - base,
                    "day_value": s.day_value, "version": world.versions[sid]})
    return out


def timeline_view(world: World, user: User, site_id: str) -> dict:
    check_site(world, user, site_id)
    b, c, r = (forward_pass(world, site_id, m) for m in ("baseline", "confirmed", "risk"))
    crit = critical_steps(world, site_id, c)
    steps = []
    for st in sorted((s for s in world.steps.values() if s.site_id == site_id), key=lambda s: b[s.id][0]):
        crews = [world.crews[bk.crew_id].name for bk in world.bookings.values() if bk.step_id == st.id]
        steps.append({"id": st.id, "code": st.code, "name": st.name, "trade": st.trade, "kind": st.kind,
                      "phase": st.phase, "weather_sensitive": st.weather_sensitive, "risk_note": st.risk_note,
                      "base": list(b[st.id]), "confirmed": list(c[st.id]), "risk": list(r[st.id]),
                      "critical": st.id in crit, "risk_flag": st.risk_days > 0, "crews": crews})
    return {"site_id": site_id, "site_name": world.sites[site_id].name, "today": TODAY, "steps": steps}


def labour_view(world: World, user: User, site_id: str) -> dict:
    check_site(world, user, site_id)
    dates = all_dates(world)
    demand: dict[str, dict[int, int]] = defaultdict(dict)
    for st in world.steps.values():
        if st.site_id == site_id and st.headcount:
            s, e = dates[site_id][st.id]
            for d in range(max(s, TODAY), min(e, TODAY + 40)):
                demand[st.trade][d] = demand[st.trade].get(d, 0) + st.headcount
    imb = [asdict(i) for i in imbalances(world, dates) if i.site_id == site_id]
    return {"site_id": site_id, "demand": {t: sorted(v.items()) for t, v in demand.items()}, "imbalances": imb}


def _option_view(world: World, user: User, o) -> dict:
    d = o.to_dict()
    target_org = world.sites[o.target_site_id].org_id if o.target_site_id else None
    if target_org and not link_active(world, user.org_id, target_org):
        d["target_anon_id"] = anon_id(o.target_site_id)
        for k in ("target_site_id", "target_step_id", "target_crew_id"):
            d.pop(k, None)
        d["parties"] = [p for p in d["parties"] if p == user.org_id] + ["a nearby project"]
        d["needs_link_with"] = "a nearby project"
    elif target_org:
        d["target_site_name"] = world.sites[o.target_site_id].name
        d["target_org_name"] = world.orgs[target_org].name
    d["needs_link"] = o.needs_link_with is not None
    return d


def sync_board_view(world: World, user: User) -> dict:
    sites = set(visible_sites(world, user))
    gaps = []
    for g in open_gaps(world):
        if g.site_id not in sites:
            continue
        st = world.steps[g.step_id]
        gaps.append({"id": g.id, "type": g.type, "site_id": g.site_id, "site_name": world.sites[g.site_id].name,
                     "step_code": st.code, "step_name": st.name, "trade": g.trade,
                     "crew": world.crews[g.crew_id].name if g.crew_id else None,
                     "start": g.start, "end": g.end, "workers": g.workers, "warning_days": g.warning_days,
                     "idle_cost_gbp": (g.end - g.start) * CREW_DAY_GBP if g.type == "SURPLUS" else 0,
                     "options": [_option_view(world, user, o) for o in options_for(world, g)]})
    outcomes = [o for o in world.outcomes if o.get("org_id") == user.org_id]
    return {"gaps": sorted(gaps, key=lambda g: g["start"]), "outcomes": outcomes,
            "days_protected": sum(o["days_protected"] for o in outcomes),
            "value_protected_gbp": sum(o["value_gbp"] for o in outcomes)}


def _nearest_km(world: World, user: User, site) -> float:
    own = [world.sites[s] for s in visible_sites(world, user)] or list(world.sites.values())
    return min(distance_km(o, site) for o in own)


def city_view(world: World, user: User) -> list[dict]:
    dates = all_dates(world)
    imb = imbalances(world, dates)
    out = []
    for sid, site in world.sites.items():
        if site.org_id == user.org_id or not site.publish or site.confidential:
            continue
        active = sorted((s for s in world.steps.values() if s.site_id == sid and s.days
                         and dates[sid][s.id][0] <= TODAY < dates[sid][s.id][1]), key=lambda s: dates[sid][s.id][0])
        phase = active[-1].phase if active else "Not started"
        windows: dict[str, set[int]] = defaultdict(set)
        for s in world.steps.values():
            if s.site_id == sid and s.headcount:
                a, e = dates[sid][s.id]
                for d in range(max(a, TODAY), min(e, TODAY + 6 * 5)):
                    windows[s.trade].add(d // 5)
        wl = [{"trade": t, "kind": "need", "week_from": min(w), "week_to": max(w)} for t, w in windows.items()]
        for i in imb:
            if i.site_id == sid and i.type == "SURPLUS":
                wl.append({"trade": i.trade, "kind": "surplus", "week_from": i.start // 5, "week_to": (i.end - 1) // 5})
        km = _nearest_km(world, user, site)
        out.append({"anon_id": anon_id(sid), "area": site.area, "distance_band": f"~{max(1, round(km))} km",
                    "phase": phase, "windows": sorted(wl, key=lambda x: (x["week_from"], x["trade"]))})
    return out


def links_view(world: World, user: User) -> list[dict]:
    out = []
    for l in world.links.values():
        if user.org_id not in (l.org_a, l.org_b):
            continue
        other = l.org_b if user.org_id == l.org_a else l.org_a
        reveal = l.status == "ACTIVE" or user.org_id == l.org_b
        out.append({"id": l.id, "status": l.status, "purpose": l.purpose, "pool": l.pool,
                    "direction": "outgoing" if user.org_id == l.org_a else "incoming",
                    "counterparty": world.orgs[other].name if reveal else "a nearby project"})
    return out


def cross_proposals_view(world: World, user: User) -> list[dict]:
    out = []
    for cp in world.cross_proposals.values():
        if user.org_id not in (cp["from_org"], cp["to_org"], cp["sub_org"]):
            continue
        agreed = cp["status"] == "AGREED"
        target_site = world.sites[world.steps[cp["target_step_id"]].site_id]
        out.append({"id": cp["id"], "status": cp["status"], "start": cp["start"], "end": cp["end"],
                    "trade": world.crews[cp["crew_id"]].trade,
                    "role": ("requester" if user.org_id == cp["from_org"] else
                             "host" if user.org_id == cp["to_org"] else "subcontractor"),
                    "your_decision": cp["accepted"].get(user.org_id),
                    "from": world.orgs[cp["from_org"]].name,
                    "target_site": target_site.name if agreed or user.org_id in (cp["to_org"], cp["sub_org"])
                    else "a nearby project",
                    "crew": world.crews[cp["crew_id"]].name if user.org_id != cp["to_org"] or agreed
                    else "a vetted M&E crew"})
    return out


def proposals_view(world: World, user: User, site_id: str) -> list[dict]:
    check_site(world, user, site_id)
    return [p for p in world.proposals.values()
            if p["site_id"] == site_id and p["org_id"] == user.org_id and p["status"] in ("PENDING", "SITE_CONFIRMED")]
