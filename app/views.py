from collections import defaultdict
from dataclasses import asdict

from app.config import CREW_DAY_GBP, TODAY
from app.domain import User, World
from app.labour import imbalances
from app.network import (anon_company, anon_id, anon_label, link_between, offer_fit, site_for_anon,
                         trade_label, view_granted)
from app.schedule import all_dates, critical_steps, forward_pass, site_finish
from app.sync_engine import distance_km, link_active, offer_state, open_gaps, options_for


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
    risks = [dict(r) for sid, r in world.risks.items() if world.steps[sid].site_id == site_id]
    return {"site_id": site_id, "site_name": world.sites[site_id].name, "today": TODAY, "steps": steps,
            "risk_signals": risks}


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
    from app.labour import effective_booking_end
    bookings = [{"crew": world.crews[b.crew_id].name, "size": world.crews[b.crew_id].size,
                 "step_code": world.steps[b.step_id].code, "trade": world.steps[b.step_id].trade,
                 "booking": [b.start, effective_booking_end(world, b)], "step_active": list(dates[site_id][b.step_id])}
                for b in sorted(world.bookings.values(), key=lambda b: (b.start, b.step_id))
                if world.steps[b.step_id].site_id == site_id and effective_booking_end(world, b) > TODAY - 5
                and b.start < TODAY + 40]
    return {"site_id": site_id, "demand": {t: sorted(v.items()) for t, v in demand.items()}, "imbalances": imb,
            "bookings": bookings}


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
    if o.mechanism == "M8":
        d["offer_state"] = offer_state(world, o.gap_id)
        live = [x for x in world.offers.values() if x.gap_id == o.gap_id and x.status not in ("WITHDRAWN", "EXPIRED")]
        d["offer_id"] = live[-1].id if live else None
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


def _phase(world: World, dates, sid: str) -> str:
    active = sorted((st for st in world.steps.values() if st.site_id == sid and st.days
                     and dates[sid][st.id][0] <= TODAY < dates[sid][st.id][1]), key=lambda st: dates[sid][st.id][0])
    return active[-1].phase if active else "Not started"


def city_view(world: World, user: User) -> list[dict]:
    from app.network import _expire_offers
    _expire_offers(world)
    dates = all_dates(world)
    out = []
    for sid, site in world.sites.items():
        if site.org_id == user.org_id or not site.publish or site.confidential:
            continue
        grants = [g for g in world.view_grants.values() if g.site_id == sid and g.viewer_org == user.org_id]
        offers = [{"id": o.id, "trade": o.trade, "trade_label": trade_label(o.trade), "workers": o.workers,
                   "start": o.start, "end": o.end, "status": o.status}
                  for o in world.offers.values() if o.site_id == sid and o.status in ("OPEN", "REQUESTED")]
        km = _nearest_km(world, user, site)
        out.append({"anon_id": anon_id(sid), "anon_label": anon_label(sid), "area": site.area,
                    "distance_band": f"~{max(1, round(km))} km", "km": round(km, 1), "phase": _phase(world, dates, sid),
                    "project_type": "Mid-rise residential", "offers": offers,
                    "view_status": grants[-1].status if grants else None,
                    "view_request_id": grants[-1].id if grants else None})
    return out


def _merge(windows: list[list[int]]) -> list[list[int]]:
    merged: list[list[int]] = []
    for s_, e_ in sorted(windows):
        if merged and s_ <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e_)
        else:
            merged.append([s_, e_])
    return merged


def _trade_windows(world: World, dates, sid: str, weeks: bool) -> dict[str, list[list[int]]]:
    by: dict[str, list[list[int]]] = defaultdict(list)
    for st in world.steps.values():
        if st.site_id != sid or not st.headcount:
            continue
        a, e = dates[sid][st.id]
        if weeks:
            a, e = (a // 5) * 5, -(-e // 5) * 5
        by[st.trade].append([a, e])
    return {t: _merge(w) for t, w in by.items()}


def trades_view(world: World, user: User, site_id: str) -> dict:
    check_site(world, user, site_id)
    dates = all_dates(world)
    idle = [{"crew": world.crews[i.crew_id].name, "crew_id": i.crew_id, "trade": i.trade, "step_code":
             world.steps[i.step_id].code, "workers": i.workers, "start": i.start, "end": i.end}
            for i in imbalances(world, dates) if i.site_id == site_id and i.type == "SURPLUS"]
    return {"site_id": site_id, "trades": _trade_windows(world, dates, site_id, weeks=False), "idle": idle,
            "trade_labels": {t: trade_label(t) for t in {st.trade for st in world.steps.values()}}}


def overlay_view(world: World, user: User, anon: str) -> dict:
    sid = site_for_anon(world, anon)
    if world.sites[sid].org_id != user.org_id and not view_granted(world, sid, user.org_id):
        raise PermissionError("the project's company hasn't shared an anonymised view with you")
    dates = all_dates(world)
    offered = [[(o.start // 5) * 5, -(-o.end // 5) * 5] for o in world.offers.values()
               if o.site_id == sid and o.status in ("OPEN", "REQUESTED", "TAKEN")]
    offered_trades = sorted({o.trade for o in world.offers.values() if o.site_id == sid
                             and o.status in ("OPEN", "REQUESTED", "TAKEN")})
    return {"anon_id": anon, "anon_label": anon_label(sid), "weeks": True,
            "trades": _trade_windows(world, dates, sid, weeks=True), "offered": offered,
            "offered_trades": offered_trades}


def offers_view(world: World, user: User) -> list[dict]:
    from app.network import _expire_offers
    _expire_offers(world)
    out = []
    for o in world.offers.values():
        base = {"id": o.id, "trade": o.trade, "trade_label": trade_label(o.trade), "workers": o.workers,
                "start": o.start, "end": o.end, "area": o.area, "status": o.status, "created_at": o.created_at}
        if o.org_id == user.org_id:
            out.append({**base, "own": True, "gap_id": o.gap_id, "site_id": o.site_id,
                        "site_name": world.sites[o.site_id].name, "crew": world.crews[o.crew_id].name})
            continue
        if o.status in ("WITHDRAWN", "EXPIRED"):
            continue
        fit = offer_fit(world, o, user.org_id)
        if not fit or user.role not in ("PM", "OPS_DIRECTOR"):
            continue
        link = next((l for l in world.links.values() if l.offer_id == o.id and l.org_a == user.org_id), None)
        if o.status != "OPEN" and link is None:
            continue  # taken by someone else
        linked = link is not None and link.status == "ACTIVE"
        out.append({**base, "own": False, "anon_id": anon_id(o.site_id), "anon_label": anon_label(o.site_id),
                    "distance_band": f"~{max(1, round(fit['km']))} km",
                    "fits": {k: fit[k] for k in ("step_id", "step_code", "step_name", "start", "end", "site_id")},
                    "counterparty": world.orgs[o.org_id].name if linked else anon_company(o.site_id),
                    "view_status": next((g.status for g in world.view_grants.values()
                                         if g.site_id == o.site_id and g.viewer_org == user.org_id), None),
                    "link_id": link.id if link else None, "link_status": link.status if link else None})
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


# ---------------------------------------------------------------- requests, trackers, notifications (spec §5.9)
def _org_name(world: World, viewer_org: str, org_id: str, site_id: str | None, revealed: bool) -> str:
    """Name a party for a viewer; the other company stays '#anon's company' until revealed."""
    if org_id == viewer_org or revealed or world.orgs[org_id].type == "SUB" or site_id is None:
        return world.orgs[org_id].name
    return anon_company(site_id)


def _sync_tracker(world: World, viewer_org: str, link, cp: dict | None) -> list[dict]:
    offer = world.offers.get(link.offer_id) if link.offer_id else None
    lender_site = offer.site_id if offer else None
    active = link.status == "ACTIVE"
    lender = _org_name(world, viewer_org, link.org_b, lender_site, active or viewer_org != link.org_a)
    borrower = world.orgs[link.org_a].name
    steps = [{"party": borrower, "label": "requests the crew", "state": "done", "at": link.created_at}]
    if link.status == "DECLINED":
        steps.append({"party": lender, "label": "declined", "state": "done", "at": link.decided_at})
        return steps
    steps.append({"party": lender, "label": "accepts and sets terms", "state": "done" if active else "wait",
                  "at": link.decided_at if active else None})
    sub_name = world.orgs[cp["sub_org"]].name if cp else "Subcontractor"
    sub_done = bool(cp and cp["accepted"].get(cp["sub_org"]))
    steps.append({"party": sub_name, "label": "accepts the move", "state": "done" if sub_done else
                  ("wait" if cp else "todo"), "at": (cp.get("decided_at") or {}).get(cp["sub_org"]) if cp else None})
    conf = (cp or {}).get("confirmed", {})
    b_done, l_done = link.org_a in conf, link.org_b in conf
    steps.append({"party": borrower, "label": "confirms booking", "state": "done" if b_done else
                  ("wait" if sub_done else "todo"), "at": conf.get(link.org_a)})
    steps.append({"party": lender, "label": "confirms booking", "state": "done" if l_done else
                  ("wait" if b_done else "todo"), "at": conf.get(link.org_b)})
    return steps


def _act(label: str, path: str, body: dict, primary: bool = True) -> dict:
    return {"label": label, "method": "POST", "path": path, "body": body, "primary": primary}


def requests_view(world: World, user: User) -> dict:
    incoming, outgoing = [], []
    pm = user.role in ("PM", "OPS_DIRECTOR")
    # anonymised view requests
    for g in world.view_grants.values():
        if user.org_id == g.owner_org and pm:
            incoming.append({"id": g.id, "kind": "view", "status": g.status, "created_at": g.created_at,
                             "title": f"{world.orgs[g.viewer_org].name} asks to see {world.sites[g.site_id].name}, "
                                      "anonymised",
                             "detail": f"They would see it as {anon_label(g.site_id)}: trade windows by week, phase "
                                       "and ~1 km area. No names, codes, exact dates or people.",
                             "counterparty": world.orgs[g.viewer_org].name,
                             "tracker": [{"party": world.orgs[g.viewer_org].name, "label": "asks", "state": "done",
                                          "at": g.created_at},
                                         {"party": world.orgs[g.owner_org].name, "label": "shares" if g.status !=
                                          "DECLINED" else "declined", "state": "wait" if g.status == "REQUESTED"
                                          else "done", "at": g.decided_at}],
                             "actions": [_act("Share anonymised view", f"/api/view-requests/{g.id}/decide",
                                              {"share": True}),
                                         _act("Decline", f"/api/view-requests/{g.id}/decide", {"share": False},
                                              False)] if g.status == "REQUESTED" else []})
        elif user.org_id == g.viewer_org and pm:
            owner = _org_name(world, user.org_id, g.owner_org, g.site_id,
                              link_between(world, g.owner_org, g.viewer_org) is not None)
            outgoing.append({"id": g.id, "kind": "view", "status": g.status, "created_at": g.created_at,
                             "title": f"Anonymised view of {anon_label(g.site_id)}", "counterparty": owner,
                             "anon_id": anon_id(g.site_id),
                             "tracker": [{"party": world.orgs[g.viewer_org].name, "label": "asks", "state": "done",
                                          "at": g.created_at},
                                         {"party": owner, "label": "shares" if g.status != "DECLINED" else "declined",
                                          "state": "wait" if g.status == "REQUESTED" else "done",
                                          "at": g.decided_at}], "actions": []})
    # crew requests (links)
    for l in world.links.values():
        cp = next((c for c in world.cross_proposals.values() if c.get("link_id") == l.id), None)
        offer = world.offers.get(l.offer_id) if l.offer_id else None
        what = f"{trade_label(offer.trade)} crew, {offer.workers} workers, days {offer.start}–{offer.end}" \
            if offer else l.purpose
        if user.org_id == l.org_b and pm:
            actions = [_act("Accept and agree pool", f"/api/links/{l.id}/decide",
                            {"accept": True, "pool_terms": {"trades": [offer.trade] if offer else [],
                                                            "return_guarantee": f"Back on "
                                                            f"{world.sites[offer.site_id].name} by day {offer.end}"
                                                            if offer else True}}),
                       _act("Decline", f"/api/links/{l.id}/decide", {"accept": False}, False)] \
                if l.status == "REQUESTED" else []
            incoming.append({"id": l.id, "kind": "crew", "status": l.status, "created_at": l.created_at,
                             "title": f"{world.orgs[l.org_a].name} requests your {what}",
                             "detail": f"Purpose: {l.purpose}. They learn it's {world.orgs[l.org_b].name} only if "
                                       "you accept.", "counterparty": world.orgs[l.org_a].name, "pool": l.pool,
                             "tracker": _sync_tracker(world, user.org_id, l, cp), "actions": actions})
        elif user.org_id == l.org_a and pm:
            revealed = l.status == "ACTIVE"
            outgoing.append({"id": l.id, "kind": "crew", "status": l.status, "created_at": l.created_at,
                             "title": f"Crew request: {what}" + (f" from {anon_label(offer.site_id)}" if offer
                                                                  and not revealed else ""),
                             "counterparty": world.orgs[l.org_b].name if revealed else
                             (anon_company(offer.site_id) if offer else "the other company"), "pool": l.pool,
                             "tracker": _sync_tracker(world, user.org_id, l, cp), "actions": []})
    # crew-move proposals to the subcontractor
    for cp in world.cross_proposals.values():
        link = world.links.get(cp.get("link_id")) if cp.get("link_id") else None
        if user.org_id == cp["sub_org"]:
            home = world.sites[world.steps[cp["home_step_id"]].site_id]
            target = world.sites[world.steps[cp["target_step_id"]].site_id]
            pending = cp["status"] in ("SENT", "PARTIAL") and cp["accepted"].get(cp["sub_org"]) is None
            incoming.append({"id": cp["id"], "kind": "proposal", "status": cp["status"], "created_at": cp["created_at"],
                             "title": f"Move {world.crews[cp['crew_id']].name} for days {cp['start']}–{cp['end']}, "
                                      "guaranteed back",
                             "detail": f"Days {cp['start']}–{cp['end']}: {world.orgs[cp['to_org']].name}, "
                                       f"{target.name} ({world.steps[cp['target_step_id']].code}). From day "
                                       f"{cp['end']}: back to {world.orgs[cp['from_org']].name}, {home.name}.",
                             "counterparty": world.orgs[cp["from_org"]].name,
                             "tracker": _sync_tracker(world, user.org_id, link, cp) if link else [],
                             "actions": [_act("Accept", f"/api/cross-proposals/{cp['id']}/decide", {"accept": True}),
                                         _act("Decline", f"/api/cross-proposals/{cp['id']}/decide",
                                              {"accept": False}, False)] if pending else []})
    # booking changes each GC confirms in its own review
    for p in world.proposals.values():
        if p.get("source", {}).get("kind") != "cross_proposal" or p["org_id"] != user.org_id or not pm:
            continue
        cp = world.cross_proposals[p["source"]["cross_proposal_id"]]
        link = world.links.get(cp.get("link_id")) if cp.get("link_id") else None
        crew = world.crews[cp["crew_id"]].name
        if p["kind"] == "add_swap_booking":
            b = p["bookings"][0]
            title = f"Add {crew} on {world.steps[b['step_id']].site_id}-{world.steps[b['step_id']].code}, " \
                    f"days {b['start']}–{b['end']}"
        else:
            mv = (p.get("booking_moves") or [{}])[0]
            st = world.steps[cp["home_step_id"]]
            title = f"Hold {crew} on {st.site_id}-{st.code} from day {mv.get('start', cp['end'])} (return guarantee)"
        incoming.append({"id": p["id"], "kind": "booking", "status": p["status"], "created_at": p.get("created_at"),
                         "title": title, "counterparty": world.orgs[cp["sub_org"]].name,
                         "tracker": _sync_tracker(world, user.org_id, link, cp) if link else [],
                         "actions": [_act("Confirm booking change", f"/api/proposals/{p['id']}/decide",
                                          {"accept": True})] if p["status"] == "PENDING" else []})
    key = lambda r: (r["status"] not in ("REQUESTED", "SENT", "PARTIAL", "PENDING"), r.get("created_at") or "")
    return {"incoming": sorted(incoming, key=key), "outgoing": sorted(outgoing, key=key)}


def notifications_view(world: World, user: User) -> list[dict]:
    return [{"id": n["id"], "text": n["text"], "at": n["at"], "read": n["read"], "ref": n.get("ref")}
            for n in reversed(world.notifications) if n["to_user"] == user.id]


def mark_read(world: World, user: User) -> dict:
    n = 0
    for x in world.notifications:
        if x["to_user"] == user.id and not x["read"]:
            x["read"] = True
            n += 1
    return {"marked": n}


def sub_bookings_view(world: World, user: User) -> list[dict]:
    if user.role != "SUB_PLANNER":
        raise PermissionError("subcontractor planners only")
    from app.labour import effective_booking_end
    dates = all_dates(world)
    mine = [b for b in world.bookings.values() if world.crews[b.crew_id].org_id == user.org_id]
    out = []
    for b in sorted(mine, key=lambda b: (b.crew_id, b.start)):
        st = world.steps[b.step_id]
        s, e = dates[st.site_id][st.id]
        end = effective_booking_end(world, b)
        if end <= TODAY - 10 or b.start >= TODAY + 60:
            continue
        others = [o for o in mine if o.crew_id == b.crew_id and o.id != b.id]
        idle_days = [d for d in range(b.start, end) if not s <= d < e and not any(
            o.start <= d < effective_booking_end(world, o)
            and dates[world.steps[o.step_id].site_id][o.step_id][0] <= d < dates[world.steps[o.step_id].site_id][o.step_id][1]
            for o in others)]
        from app.labour import _runs
        out.append({"crew": world.crews[b.crew_id].name, "crew_id": b.crew_id, "site_name": world.sites[st.site_id].name,
                    "org_name": world.orgs[world.sites[st.site_id].org_id].name, "step_code": st.code,
                    "step_name": st.name, "booking": [b.start, end], "step_active": [s, e],
                    "idle": [list(r) for r in _runs(idle_days)]})
    return out


def report_view(world: World, user: User) -> dict:
    rows = [o for o in world.outcomes if o.get("org_id") == user.org_id]
    return {"days_protected": sum(o["days_protected"] for o in rows),
            "value_gbp": sum(o["value_gbp"] for o in rows),
            "idle_crew_days_used": sum(o.get("idle_crew_days_used", 0) for o in rows),
            "day_value": next((world.sites[s].day_value for s in visible_sites(world, user)), None),
            "rows": [{"event": o.get("event"), "no_action_finish": o.get("no_action_finish"),
                      "outcome_finish": o.get("outcome_finish"), "protected_days": o["days_protected"],
                      "mechanism": o.get("mechanism"), "evidence": o.get("evidence")} for o in rows]}


def events_view(world: World, user: User) -> list[dict]:
    return [e for e in world.events if e.get("org_id") == user.org_id]
