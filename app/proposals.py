import copy
from dataclasses import asdict

from app.config import PM_CRITICAL_SLIP_DAYS
from app.domain import Booking, User, World
from app.labour import diff_imbalances, imbalances
from app.schedule import all_dates, critical_steps, forward_pass, site_finish


class StaleProposal(Exception):
    pass


def _apply(world: World, changes: list[dict]) -> None:
    for c in changes:
        if c["field"] != "delay_days":
            raise ValueError(f"unsupported field {c['field']}")
        world.steps[c["step_id"]].delay_days = c["to"]


def _validate(world: World, site_id: str, changes: list[dict]) -> None:
    for c in changes:
        st = world.steps.get(c["step_id"])
        if st is None or st.site_id != site_id:
            raise ValueError(f"unknown step {c['step_id']} for site {site_id}")
        if not 0 <= c["to"] <= 60:
            raise ValueError("delay must be between 0 and 60 working days")


def build_proposal(world: World, user: User, site_id: str, changes: list[dict], source: dict) -> dict:
    _validate(world, site_id, changes)
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
    changes = [{**c, "from": world.steps[c["step_id"]].delay_days} for c in changes]
    p = {"id": world.next_id("prop"), "site_id": site_id, "org_id": world.sites[site_id].org_id,
         "created_by": user.id, "based_on_version": world.versions[site_id], "changes": changes,
         "source": source, "status": "PENDING", "needs_pm": finish_to != finish_from or slip_on_critical,
         "knock_on": {"moved": moved, "finish_from": finish_from, "finish_to": finish_to,
                      "labour": {k: [asdict(i) for i in v] for k, v in diff.items()}}}
    world.proposals[p["id"]] = p
    world.log("ProposalCreated", user.id, site_id, {"proposal_id": p["id"]}, source)
    return p


def decide_proposal(world: World, user: User, pid: str, accept: bool) -> dict:
    p = world.proposals[pid]
    if user.org_id != p["org_id"]:
        raise PermissionError("not your company's proposal")
    if user.role == "SITE_MANAGER" and p["site_id"] not in user.site_ids:
        raise PermissionError("not your site")
    if p["status"] in ("APPLIED", "REJECTED") or p["based_on_version"] != world.versions[p["site_id"]]:
        raise StaleProposal(pid)
    if not accept:
        p["status"] = "REJECTED"
        world.log("ProposalRejected", user.id, p["site_id"], {"proposal_id": pid})
        return {"status": "REJECTED"}
    if p["needs_pm"] and user.role != "PM":
        p["status"] = "SITE_CONFIRMED"
        world.log("ProposalSiteConfirmed", user.id, p["site_id"], {"proposal_id": pid})
        return {"status": "SITE_CONFIRMED"}
    if "bookings" in p:
        for b in p["bookings"]:
            world.bookings[b["id"]] = Booking(**b)
    else:
        _apply(world, p["changes"])
    p["status"] = "APPLIED"
    world.versions[p["site_id"]] += 1
    world.snapshots.append({"site_id": p["site_id"], "version": world.versions[p["site_id"]],
                            "dates": forward_pass(world, p["site_id"], "confirmed")})
    world.log("ForecastConfirmed", user.id, p["site_id"], {"proposal_id": pid, "changes": p["changes"]})
    src = p.get("source", {})
    if src.get("kind") == "cross_proposal" and p.get("kind") == "confirm_return":
        cp = world.cross_proposals[src["cross_proposal_id"]]
        world.option_states[cp["option_id"]] = "DONE"
        world.outcomes.append({"option_id": cp["option_id"], "org_id": p["org_id"],
                               "days_protected": cp["days_protected"], "value_gbp": cp["value_gbp"]})
    return {"status": "APPLIED", "version": world.versions[p["site_id"]]}


def booking_proposal(world: World, cp: dict, org_id: str, kind: str) -> dict:
    target_site = world.steps[cp["target_step_id"]].site_id
    home_site = world.steps[cp["home_step_id"]].site_id
    site_id = target_site if kind == "add_swap_booking" else home_site
    bookings = []
    if kind == "add_swap_booking":
        bid = world.next_id("bk")
        bookings.append({"id": bid, "crew_id": cp["crew_id"], "step_id": cp["target_step_id"],
                         "start": cp["start"], "end": cp["end"], "source": f"swap:{cp['id']}"})
    p = {"id": world.next_id("prop"), "site_id": site_id, "org_id": org_id, "created_by": "system",
         "based_on_version": world.versions[site_id], "changes": [], "bookings": bookings,
         "source": {"kind": "cross_proposal", "cross_proposal_id": cp["id"]}, "status": "PENDING",
         "needs_pm": True, "kind": kind,
         "knock_on": {"moved": [], "finish_from": None, "finish_to": None,
                      "labour": {"created": [], "resolved": []}}}
    world.proposals[p["id"]] = p
    world.log("ProposalCreated", None, site_id, {"proposal_id": p["id"], "kind": kind},
              {"kind": "cross_proposal", "cross_proposal_id": cp["id"]})
    return p
