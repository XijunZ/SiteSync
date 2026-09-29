import hashlib

from app.domain import Link, User, World


def anon_id(site_id: str) -> str:
    return hashlib.sha1(f"sitesync:{site_id}".encode()).hexdigest()[:8]


def site_for_anon(world: World, anon: str) -> str:
    for sid in world.sites:
        if anon_id(sid) == anon:
            return sid
    raise ValueError(f"unknown project {anon}")


def request_link(world: World, user: User, anon: str, purpose: str) -> Link:
    target_org = world.sites[site_for_anon(world, anon)].org_id
    if target_org == user.org_id:
        raise ValueError("cannot link with your own company")
    link = Link(world.next_id("link"), user.org_id, target_org, user.id, purpose)
    world.links[link.id] = link
    world.log("LinkRequested", user.id, None, {"link_id": link.id, "to_org": target_org, "purpose": purpose})
    return link


def decide_link(world: World, user: User, link_id: str, accept: bool, pool_terms: dict | None = None) -> Link:
    link = world.links.get(link_id)
    if link is None:
        raise ValueError(f"unknown link {link_id}")
    if user.org_id != link.org_b or user.role not in ("PM", "OPS_DIRECTOR"):
        raise PermissionError("only the target company's PM can decide")
    link.status = "ACTIVE" if accept else "DECLINED"
    link.pool = (pool_terms or {"trades": [], "return_guarantee": True}) if accept else None
    world.log("LinkAccepted" if accept else "LinkDeclined", user.id, None, {"link_id": link_id, "pool": link.pool})
    return link


def send_cross_proposal(world: World, user: User, gap, opt) -> dict:
    cp = {"id": world.next_id("cp"), "option_id": opt.id, "gap_id": gap.id, "from_org": user.org_id,
          "to_org": world.sites[opt.target_site_id].org_id, "sub_org": world.crews[gap.crew_id].org_id,
          "crew_id": gap.crew_id, "home_step_id": gap.step_id, "target_step_id": opt.target_step_id,
          "start": gap.start, "end": gap.end, "accepted": {}, "status": "SENT",
          "days_protected": opt.days_protected, "value_gbp": opt.value_gbp}
    world.cross_proposals[cp["id"]] = cp
    world.log("ProposalSent", user.id, gap.site_id, {"cross_proposal_id": cp["id"]})
    return cp


def decide_cross_proposal(world: World, user: User, cp_id: str, accept: bool) -> dict:
    cp = world.cross_proposals.get(cp_id)
    if cp is None:
        raise ValueError(f"unknown proposal {cp_id}")
    if user.org_id not in (cp["to_org"], cp["sub_org"]):
        raise PermissionError("not a party to this proposal")
    if cp["status"] in ("AGREED", "DECLINED"):
        raise ValueError(f"proposal already {cp['status'].lower()}")
    cp["accepted"][user.org_id] = accept
    world.log("ProposalAccepted" if accept else "ProposalDeclined", user.id, None, {"cross_proposal_id": cp_id})
    if not accept:
        cp["status"] = "DECLINED"
        world.option_states[cp["option_id"]] = "FAILED"
        return {"status": "DECLINED", "proposals": []}
    if all(cp["accepted"].get(o) for o in (cp["to_org"], cp["sub_org"])):
        cp["status"] = "AGREED"
        from app.proposals import booking_proposal
        p1 = booking_proposal(world, cp, org_id=cp["to_org"], kind="add_swap_booking")
        p2 = booking_proposal(world, cp, org_id=cp["from_org"], kind="confirm_return")
        return {"status": "AGREED", "proposals": [p1, p2]}
    cp["status"] = "PARTIAL"
    return {"status": "PARTIAL", "proposals": []}
