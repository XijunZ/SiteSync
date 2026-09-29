import math
from dataclasses import asdict, dataclass, field

from app.config import CREW_DAY_GBP, MAX_SWAP_KM, RETURN_LAG_DAYS, TODAY
from app.domain import User, World
from app.labour import imbalances
from app.schedule import all_dates, critical_steps, forward_pass, site_finish

RELIABILITY = {"M1": 3, "M3": 3, "M8": 2, "M10": 2, "M13": 2}


@dataclass
class Gap:
    id: str
    type: str
    site_id: str
    step_id: str
    crew_id: str | None
    trade: str
    start: int
    end: int
    workers: int
    warning_days: int


@dataclass
class Option:
    id: str
    gap_id: str
    mechanism: str
    title: str
    feasible: bool
    reason: str | None
    setup_days: int
    start_by: int
    days_protected: int
    idle_cost_avoided_gbp: int
    value_gbp: int
    parties: list[str] = field(default_factory=list)
    target_site_id: str | None = None
    target_step_id: str | None = None
    target_crew_id: str | None = None
    needs_link_with: str | None = None
    distance_km: float | None = None
    status: str = "PROPOSED"

    def to_dict(self) -> dict:
        return asdict(self)


def distance_km(a, b) -> float:
    r = 6371.0
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dp, dl = p2 - p1, math.radians(b.lon - a.lon)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def link_active(world: World, a: str, b: str) -> bool:
    return a == b or any(l.status == "ACTIVE" and {l.org_a, l.org_b} == {a, b} for l in world.links.values())


def gap_id(i) -> str:
    return f"{i.type}:{i.step_id}:{i.crew_id}:{i.start}-{i.end}"


def gap_days(gap: "Gap") -> int:
    return gap.end - gap.start


def open_gaps(world: World) -> list[Gap]:
    return [Gap(gap_id(i), i.type, i.site_id, i.step_id, i.crew_id, i.trade, i.start, i.end, i.workers,
                i.start - TODAY) for i in imbalances(world, all_dates(world))]


def _days_protected(world: World, gap: Gap) -> int:
    dates = forward_pass(world, gap.site_id, "confirmed")
    if gap.type != "SURPLUS" or gap.step_id not in critical_steps(world, gap.site_id, dates):
        return 0
    home_start = dates[gap.step_id][0]
    late = forward_pass(world, gap.site_id, "confirmed",
                        min_start={gap.step_id: home_start + RETURN_LAG_DAYS})
    return site_finish(late) - site_finish(dates)


def _base(world, gap, mech, title, feasible, reason, setup, dp, idle=0, **kw) -> Option:
    day_value = world.sites[gap.site_id].day_value
    return Option(id=f"{gap.id}|{mech}", gap_id=gap.id, mechanism=mech, title=title, feasible=feasible,
                  reason=reason, setup_days=setup, start_by=gap.start - setup, days_protected=dp,
                  idle_cost_avoided_gbp=idle, value_gbp=dp * day_value + idle, **kw)


def _m1(world, gap, dp) -> Option:
    dates = all_dates(world)
    same = [s for s in world.steps.values() if s.site_id == gap.site_id and s.trade == gap.trade
            and s.id != gap.step_id and s.has_crew
            and dates[s.site_id][s.id][0] < gap.end and dates[s.site_id][s.id][1] > gap.start]
    free = [s for s in same if not any(b.step_id == s.id for b in world.bookings.values())]
    if free:
        return _base(world, gap, "M1", f"Resequence: crew works {free[0].code} ({free[0].name}) first",
                     True, None, 0, dp, gap_days(gap) * CREW_DAY_GBP, target_step_id=free[0].id)
    staffed = ", ".join(f"{s.code} staffed by {world.crews[b.crew_id].name}" for s in same
                        for b in world.bookings.values() if b.step_id == s.id)
    return _base(world, gap, "M1", "Resequence on site", False,
                 f"No unstaffed ready {gap.trade} work on site ({staffed or 'none active'})", 0, dp)


def _m3(world, gap, dp) -> Option:
    return _base(world, gap, "M3", "Re-slot crew to new dates and notify downstream trades", True, None, 0, dp,
                 parties=[world.sites[gap.site_id].org_id])


def _overlap_ok(world: World, dates, gap: Gap, step_id: str) -> bool:
    st = world.steps[step_id]
    s, e = dates[st.site_id][st.id]
    return min(e, gap.end) - max(s, gap.start) >= min(3, gap_days(gap))


def _swap_candidates_memory(world: World, gap: Gap) -> list[tuple]:
    """(target_step_id, target_crew_id, km) for the same sub's bookings on other sites active in the gap."""
    crew = world.crews[gap.crew_id]
    home = world.sites[gap.site_id]
    dates = all_dates(world)
    out = []
    for b in world.bookings.values():
        c = world.crews[b.crew_id]
        st = world.steps[b.step_id]
        if c.org_id != crew.org_id or st.site_id == gap.site_id or st.trade != gap.trade:
            continue
        target_gc = world.sites[st.site_id].org_id
        approved = any(a.sub_org_id == crew.org_id and a.gc_org_id == target_gc for a in world.approvals)
        km = distance_km(home, world.sites[st.site_id])
        if _overlap_ok(world, dates, gap, st.id) and approved and km <= MAX_SWAP_KM:
            out.append((st.id, b.crew_id, km))
    return sorted(out, key=lambda t: (t[2], t[0]))


def swap_candidates_neo4j(world: World, gap: Gap, mirror) -> list[tuple]:
    """Same result, with approval, distance and trade matched in Cypher; date overlap from the engine."""
    dates = all_dates(world)
    rows = mirror.swap_candidates(world.crews[gap.crew_id].org_id, gap.site_id, gap.trade, MAX_SWAP_KM)
    out = [(r["step_id"], r["crew_id"], r["km"]) for r in rows if _overlap_ok(world, dates, gap, r["step_id"])]
    return sorted(out, key=lambda t: (t[2], t[0]))


def swap_candidates(world: World, gap: Gap) -> list[tuple]:
    from app.graph_neo4j import get_mirror
    mirror = get_mirror()
    if mirror:
        try:
            return swap_candidates_neo4j(world, gap, mirror)
        except Exception:  # noqa: BLE001 - fall back to the in-memory search
            pass
    return swap_candidates_memory(world, gap)


def _m8(world, gap, dp) -> Option | None:
    if gap.type != "SURPLUS":
        return None
    cands = swap_candidates(world, gap)
    if not cands:
        return None
    step_id, crew2, km = cands[0]
    target_site = world.steps[step_id].site_id
    home_gc, target_gc = world.sites[gap.site_id].org_id, world.sites[target_site].org_id
    home_start = forward_pass(world, gap.site_id, "confirmed")[gap.step_id][0]
    returns_ok = gap.end <= home_start
    linked = link_active(world, home_gc, target_gc)
    # Offering idle days needs no link: the borrower's crew request creates it (spec §5.7).
    feasible = returns_ok
    reason = None if feasible else "Crew would not return in time"
    sub = world.orgs[world.crews[gap.crew_id].org_id].name
    return _base(world, gap, "M8",
                 f"Slot swap: {sub} crew works a nearby project days {gap.start}–{gap.end}, "
                 f"back on site day {home_start}",
                 feasible, reason, 1, dp, gap_days(gap) * CREW_DAY_GBP,
                 parties=[home_gc, target_gc, world.crews[gap.crew_id].org_id], target_site_id=target_site,
                 target_step_id=step_id, target_crew_id=crew2,
                 needs_link_with=None if linked else target_gc, distance_km=km)


def _m10(world, gap) -> Option | None:
    if gap.type != "SHORTAGE":
        return None
    gc = world.sites[gap.site_id].org_id
    agencies = [a for a in world.approvals if a.gc_org_id == gc and world.orgs[a.sub_org_id].type == "AGENCY"]
    if not agencies:
        return None
    a = agencies[0]
    ok = a.setup_days <= gap.warning_days
    return _base(world, gap, "M10", f"Agency top-up via {world.orgs[a.sub_org_id].name} (agency premium ~35–65%)",
                 ok, None if ok else "Not enough warning", a.setup_days, 0, parties=[gc, a.sub_org_id])


def _m13(world, gap) -> Option | None:
    """Request capacity from nearby projects: publish an anonymised need (trade, workers, window, area)."""
    if gap.type != "SHORTAGE":
        return None
    gc = world.sites[gap.site_id].org_id
    return _base(world, gap, "M13", f"Request {gap.workers} {gap.trade.upper() if gap.trade == 'mep' else gap.trade} "
                 "workers from nearby projects (anonymised)", True, None, 0, 0, parties=[gc])


def options_for(world: World, gap: Gap) -> list[Option]:
    dp = _days_protected(world, gap)
    opts = [o for o in [_m1(world, gap, dp) if gap.type == "SURPLUS" else None,
                        _m3(world, gap, dp) if gap.type == "SURPLUS" else None,
                        _m8(world, gap, dp), _m13(world, gap), _m10(world, gap)] if o]
    for o in opts:
        o.status = world.option_states.get(o.id, "PROPOSED")
        if o.status == "PROPOSED" and TODAY > o.start_by:
            o.status = "EXPIRED"
    return sorted(opts, key=lambda o: (not o.feasible, -o.value_gbp, -RELIABILITY.get(o.mechanism, 1),
                                       o.setup_days))


def offer_state(world: World, gap_id_: str) -> str:
    """none | offered | requested | agreed | done for the M8 offer of a gap."""
    offers = [o for o in world.offers.values() if o.gap_id == gap_id_ and o.status not in ("WITHDRAWN", "EXPIRED")]
    if not offers:
        return "none"
    o = offers[-1]
    if o.status == "OPEN":
        return "offered"
    if o.status == "REQUESTED":
        return "requested"
    cps = [c for c in world.cross_proposals.values() if c["gap_id"] == gap_id_]
    return "done" if cps and cps[-1]["status"] == "DONE" else "agreed"


def approve_option(world: World, user: User, gap_id_: str, mechanism: str,
                   target_step_id: str | None = None) -> dict:
    gap = next((g for g in open_gaps(world) if g.id == gap_id_), None)
    if gap is None:
        raise ValueError("gap no longer open")
    opt = next((o for o in options_for(world, gap) if o.mechanism == mechanism), None)
    if opt is None or not opt.feasible:
        raise ValueError((opt.reason if opt else None) or "option not available")
    world.option_states[opt.id] = "APPROVED"
    world.log("OptionApproved", user.id, gap.site_id, {"option_id": opt.id, "mechanism": mechanism})
    if mechanism == "M3":
        home_start, home_end = forward_pass(world, gap.site_id, "confirmed")[gap.step_id]
        for b in world.bookings.values():
            if b.step_id == gap.step_id and b.crew_id == gap.crew_id:
                b.start, b.end = home_start, home_end - world.steps[gap.step_id].delay_days
        world.option_states[opt.id] = "DONE"
        from app.network import _latest_cause
        cause = _latest_cause(world, gap.site_id)
        world.outcomes.append({"option_id": opt.id, "org_id": user.org_id, "mechanism": "M3 re-slot",
                               "days_protected": opt.days_protected,
                               "value_gbp": opt.days_protected * world.sites[gap.site_id].day_value,
                               "idle_cost_avoided_gbp": 0, "idle_crew_days_used": 0,
                               "no_action_finish": site_finish(forward_pass(world, gap.site_id, "confirmed"))
                               + opt.days_protected,
                               "outcome_finish": site_finish(forward_pass(world, gap.site_id, "confirmed")),
                               "event": cause["event"], "evidence": cause["evidence"]})
        world.log("BookingChanged", user.id, gap.site_id, {"crew_id": gap.crew_id, "step_id": gap.step_id})
        return {"status": "DONE", "option": opt.to_dict()}
    if mechanism == "M8":
        from app.network import send_cross_proposal
        target_gc = world.sites[world.steps[target_step_id or opt.target_step_id].site_id].org_id
        if not link_active(world, user.org_id, target_gc):
            world.option_states.pop(opt.id, None)
            raise ValueError("Offer the idle days first; the borrower's crew request creates the link")
        cp = send_cross_proposal(world, user, gap, opt, target_step_id=target_step_id)
        world.option_states[opt.id] = "IN_PROGRESS"
        return {"status": "IN_PROGRESS", "cross_proposal_id": cp["id"], "option": opt.to_dict()}
    return {"status": "APPROVED", "option": opt.to_dict()}


def swap_candidates_memory(world: World, gap: Gap) -> list[tuple]:
    import time
    from app.graph_neo4j import SWAP_CYPHER, record
    t0 = time.perf_counter()
    out = _swap_candidates_memory(world, gap)
    record("swap candidates", SWAP_CYPHER, (time.perf_counter() - t0) * 1000, len(out), "memory")
    return out
