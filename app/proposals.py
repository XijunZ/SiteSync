import copy
from dataclasses import asdict

from app.config import LOOKAHEAD_DAYS, PM_CRITICAL_SLIP_DAYS, TODAY
from app.domain import Booking, User, World
from app.labour import diff_imbalances, imbalances
from app.schedule import all_dates, critical_steps, forward_pass, natural_start, site_finish

FIELDS = {"delay_days", "lag_days"}


class StaleProposal(Exception):
    pass


def _apply(world: World, changes: list[dict]) -> None:
    for c in changes:
        if c["field"] not in FIELDS:
            raise ValueError(f"unsupported field {c['field']}")
        setattr(world.steps[c["step_id"]], c["field"], c["to"])


def _validate(world: World, site_id: str, changes: list[dict]) -> None:
    for c in changes:
        st = world.steps.get(c["step_id"])
        if st is None or st.site_id != site_id:
            raise ValueError(f"unknown step {c['step_id']} for site {site_id}")
        if c["field"] not in FIELDS:
            raise ValueError(f"unsupported field {c['field']}")
        if c["field"] == "delay_days" and not -st.days <= c["to"] <= 60:
            raise ValueError("delay must be between 0 and 60 working days")
        if c["field"] == "lag_days" and not 0 <= c["to"] <= 60:
            raise ValueError("start can move at most 60 working days")


def _extensions(world: World, changes: list[dict]) -> list[dict]:
    """EXTEND entries: a delayed step's own booking is assumed extended to match (spec §5.2)."""
    out = []
    for c in changes:
        if c["field"] != "delay_days":
            continue
        st = world.steps[c["step_id"]]
        grow = c["to"] - st.delay_days
        if grow <= 0:
            continue
        for b in world.bookings.values():
            if b.step_id == st.id:
                old_end = b.end + st.delay_days
                crew = world.crews[b.crew_id]
                out.append({"type": "EXTEND", "site_id": st.site_id, "step_id": st.id, "crew_id": b.crew_id,
                            "trade": crew.trade, "start": old_end, "end": old_end + grow, "workers": crew.size})
    return out


def knock_on(world: World, site_id: str, changes: list[dict]) -> dict:
    """Dates and labour consequences of `changes`, computed on a copy (nothing is saved)."""
    before_dates = forward_pass(world, site_id, "confirmed")
    before_imb = imbalances(world, all_dates(world))
    sim = copy.deepcopy(world)
    _apply(sim, changes)
    after_dates = forward_pass(sim, site_id, "confirmed")
    after_imb = imbalances(sim, all_dates(sim))
    crit = critical_steps(world, site_id, before_dates)
    moved = [{"step_id": k, "code": world.steps[k].code, "from": list(before_dates[k]), "to": list(after_dates[k])}
             for k in before_dates if before_dates[k] != after_dates[k]]
    finish_from, finish_to = site_finish(before_dates), site_finish(after_dates)
    slip_on_critical = any(m["step_id"] in crit and m["to"][1] - m["from"][1] >= PM_CRITICAL_SLIP_DAYS
                           for m in moved)
    diff = diff_imbalances(before_imb, after_imb)
    labour = {k: [asdict(i) for i in v] for k, v in diff.items()}
    labour["created"] += _extensions(world, changes)
    return {"moved": moved, "finish_from": finish_from, "finish_to": finish_to, "labour": labour,
            "needs_pm": finish_to != finish_from or slip_on_critical}


def build_proposal(world: World, user: User, site_id: str, changes: list[dict], source: dict) -> dict:
    _validate(world, site_id, changes)
    k = knock_on(world, site_id, changes)
    changes = [{**c, "from": getattr(world.steps[c["step_id"]], c["field"])} for c in changes]
    p = {"id": world.next_id("prop"), "site_id": site_id, "org_id": world.sites[site_id].org_id,
         "created_by": user.id, "created_at": world.now(), "based_on_version": world.versions[site_id],
         "changes": changes, "source": source, "status": "PENDING", "needs_pm": k.pop("needs_pm"), "knock_on": k}
    world.proposals[p["id"]] = p
    world.log("ProposalCreated", user.id, site_id, {"proposal_id": p["id"]}, source)
    return p


def edit_to_changes(world: World, site_id: str, step_id: str, start: int | None, finish: int | None) -> list[dict]:
    """Turn a timeline bar edit (new start and/or finish) into lag/delay changes. Raises ValueError."""
    st = world.steps.get(step_id)
    if st is None or st.site_id != site_id:
        raise ValueError(f"unknown step {step_id} for site {site_id}")
    cur_s, cur_e = forward_pass(world, site_id, "confirmed")[step_id]
    start = cur_s if start is None else int(start)
    finish = cur_e if finish is None else int(finish)
    if finish < start:
        raise ValueError("Finish can't be before start.")
    nat = natural_start(world, site_id, step_id)
    if start < nat:
        raise ValueError(f"Start can't be before its predecessors finish (day {nat}).")
    lag, delay = start - nat, (finish - start) - st.days
    changes = []
    if lag != st.lag_days:
        changes.append({"step_id": step_id, "field": "lag_days", "to": lag})
    if delay != st.delay_days:
        changes.append({"step_id": step_id, "field": "delay_days", "to": delay})
    if not changes:
        raise ValueError("No change yet. Edit the dates to see the knock-on.")
    return changes


def preview_edit(world: World, user: User, site_id: str, step_id: str, start, finish) -> dict:
    from app.views import check_site
    check_site(world, user, site_id)
    try:
        changes = edit_to_changes(world, site_id, step_id, start, finish)
        _validate(world, site_id, changes)
    except ValueError as e:
        return {"moved_count": None, "finish_from": None, "finish_to": None, "new_gaps_in_lookahead": None,
                "labour": {"created": [], "resolved": []}, "error": str(e)}
    k = knock_on(world, site_id, changes)
    new_gaps = [g for g in k["labour"]["created"]
                if g["type"] != "EXTEND" and g["start"] < TODAY + LOOKAHEAD_DAYS and g["end"] > TODAY]
    return {"moved_count": len([m for m in k["moved"] if m["step_id"] != step_id]),
            "finish_from": k["finish_from"], "finish_to": k["finish_to"], "new_gaps_in_lookahead": len(new_gaps),
            "labour": k["labour"], "needs_pm": k["needs_pm"], "error": None}


def decide_proposal(world: World, user: User, pid: str, accept: bool) -> dict:
    p = world.proposals[pid]
    if user.org_id != p["org_id"]:
        raise PermissionError("not your company's proposal")
    if user.role == "SITE_MANAGER" and p["site_id"] not in user.site_ids:
        raise PermissionError("not your site")
    if p["status"] in ("APPLIED", "REJECTED") or p["based_on_version"] != world.versions[p["site_id"]]:
        raise StaleProposal(pid)
    site = world.sites[p["site_id"]]
    if not accept:
        p["status"] = "REJECTED"
        world.log("ProposalRejected", user.id, p["site_id"], {"proposal_id": pid})
        return {"status": "REJECTED"}
    if p["needs_pm"] and user.role != "PM":
        p["status"] = "SITE_CONFIRMED"
        p["site_confirmed"] = {"by": user.name, "at": world.now()}
        world.log("ProposalSiteConfirmed", user.id, p["site_id"], {"proposal_id": pid})
        world.notify([u for u in world.pms_of(p["org_id"]) if u != user.id],
                     f"{user.name} confirmed a change on {site.name}; the handover moves, so it needs your approval.",
                     pid)
        return {"status": "SITE_CONFIRMED"}
    if "bookings" in p:
        for b in p["bookings"]:
            world.bookings[b["id"]] = Booking(**b)
        for mv in p.get("booking_moves", []):
            b = world.bookings[mv["booking_id"]]
            b.start, b.end = mv["start"], mv["end"]
    else:
        _apply(world, p["changes"])
        for c in p["changes"]:  # a confirmed fact supersedes the risk signal on that step
            if c["field"] == "delay_days" and world.steps[c["step_id"]].risk_days:
                world.steps[c["step_id"]].risk_days = 0
                world.risks.pop(c["step_id"], None)
                world.log("RiskFlagCleared", user.id, p["site_id"], {"step_id": c["step_id"], "by": "confirmed fact"})
    p["status"] = "APPLIED"
    p["applied"] = {"by": user.name, "at": world.now()}
    world.versions[p["site_id"]] += 1
    world.snapshots.append({"site_id": p["site_id"], "version": world.versions[p["site_id"]],
                            "dates": forward_pass(world, p["site_id"], "confirmed")})
    world.log("ForecastConfirmed", user.id, p["site_id"], {"proposal_id": pid, "changes": p["changes"]})
    if p["created_by"] not in ("system", user.id) and p["created_by"] in world.users:
        world.notify(p["created_by"], f"{user.name} approved your change on {site.name}.", pid)
    src = p.get("source", {})
    if src.get("kind") == "cross_proposal":
        _after_booking_confirmed(world, user, p, src["cross_proposal_id"])
    return {"status": "APPLIED", "version": world.versions[p["site_id"]]}


def _after_booking_confirmed(world: World, user: User, p: dict, cp_id: str) -> None:
    cp = world.cross_proposals[cp_id]
    cp.setdefault("confirmed", {})[p["org_id"]] = world.now()
    lender, borrower = cp["from_org"], cp["to_org"]
    if p.get("kind") == "add_swap_booking":
        world.notify(world.pms_of(lender), f"{world.orgs[borrower].name} confirmed the crew booking on their site. "
                                           "Confirm yours to complete the sync.", cp_id)
    if p.get("kind") == "confirm_return":
        world.option_states[cp["option_id"]] = "DONE"
        cp["status"] = "DONE"
        world.outcomes.append({"option_id": cp["option_id"], "org_id": p["org_id"], "mechanism": "M8 slot swap",
                               "days_protected": cp["days_protected"],
                               "value_gbp": cp["days_protected"] * world.sites[p["site_id"]].day_value,
                               "idle_cost_avoided_gbp": cp.get("idle_cost_avoided_gbp", 0),
                               "idle_crew_days_used": cp["end"] - cp["start"],
                               "no_action_finish": cp.get("no_action_finish"),
                               "outcome_finish": site_finish(forward_pass(world, p["site_id"], "confirmed")),
                               "event": cp.get("event"), "evidence": cp.get("evidence")})
        for org in (borrower, cp["sub_org"]):
            world.notify(world.users_of(org), "Sync complete: the crew move is confirmed by both companies.", cp_id)
        world.log("OutcomeRecorded", user.id, p["site_id"], {"cross_proposal_id": cp_id,
                                                               "days_protected": cp["days_protected"]})


def booking_proposal(world: World, cp: dict, org_id: str, kind: str) -> dict:
    target_site = world.steps[cp["target_step_id"]].site_id
    home_site = world.steps[cp["home_step_id"]].site_id
    site_id = target_site if kind == "add_swap_booking" else home_site
    bookings, moves = [], []
    if kind == "add_swap_booking":
        bid = world.next_id("bk")
        bookings.append({"id": bid, "crew_id": cp["crew_id"], "step_id": cp["target_step_id"],
                         "start": cp["start"], "end": cp["end"], "source": f"swap:{cp['id']}"})
    else:  # hold the crew to the home step's new dates (return guarantee)
        st = world.steps[cp["home_step_id"]]
        s, e = forward_pass(world, site_id, "confirmed")[st.id]
        for b in world.bookings.values():
            if b.step_id == st.id and b.crew_id == cp["crew_id"]:
                moves.append({"booking_id": b.id, "start": s, "end": e - st.delay_days,
                              "from": [b.start, b.end]})
    p = {"id": world.next_id("prop"), "site_id": site_id, "org_id": org_id, "created_by": "system",
         "created_at": world.now(), "based_on_version": world.versions[site_id], "changes": [],
         "bookings": bookings, "booking_moves": moves,
         "source": {"kind": "cross_proposal", "cross_proposal_id": cp["id"]}, "status": "PENDING",
         "needs_pm": True, "kind": kind,
         "knock_on": {"moved": [], "finish_from": None, "finish_to": None,
                      "labour": {"created": [], "resolved": []}}}
    world.proposals[p["id"]] = p
    world.log("ProposalCreated", None, site_id, {"proposal_id": p["id"], "kind": kind},
              {"kind": "cross_proposal", "cross_proposal_id": cp["id"]})
    return p
