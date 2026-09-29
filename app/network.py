"""Cross-company flow (spec §5.7): the lender offers, the borrower asks, the lender decides."""
import hashlib

from app.config import MAX_SWAP_KM, TODAY
from app.domain import Link, Offer, User, ViewGrant, World

DEFAULT_POOL = {"trades": ["mep"], "recharge": "Sub's agreed day rate", "return_guarantee": True,
                "priority_rule": "Critical path wins", "notice_days": 5}
LIVE_OFFER = ("OPEN", "REQUESTED")


def anon_id(site_id: str) -> str:
    return hashlib.sha1(f"sitesync:{site_id}".encode()).hexdigest()[:8]


def anon_label(site_id: str) -> str:
    return "#" + anon_id(site_id)[:3].upper()


def anon_company(site_id: str) -> str:
    return f"{anon_label(site_id)}'s company"


def site_for_anon(world: World, anon: str) -> str:
    for sid in world.sites:
        if anon_id(sid) == anon:
            return sid
    raise ValueError(f"unknown project {anon}")


def link_between(world: World, a: str, b: str) -> Link | None:
    for l in world.links.values():
        if {l.org_a, l.org_b} == {a, b} and l.status == "ACTIVE":
            return l
    return None


def _require_pm(user: User) -> None:
    if user.role not in ("PM", "OPS_DIRECTOR"):
        raise PermissionError("only a PM can do this")


# ---------------------------------------------------------------- offers
def offer_fit(world: World, offer: Offer, org_id: str) -> dict | None:
    """The borrower's own step of the offered trade whose confirmed window overlaps the offer, within 10 km."""
    from app.schedule import all_dates
    from app.sync_engine import distance_km
    lender_site = world.sites[offer.site_id]
    dates = all_dates(world)
    best = None
    for st in world.steps.values():
        site = world.sites[st.site_id]
        if site.org_id != org_id or st.trade != offer.trade or not st.headcount:
            continue
        if distance_km(lender_site, site) > MAX_SWAP_KM:
            continue
        s, e = dates[st.site_id][st.id]
        overlap = min(e, offer.end) - max(s, offer.start)
        if overlap > 0 and (best is None or overlap > best[0]):
            best = (overlap, st, s, e, distance_km(lender_site, site))
    if not best:
        return None
    _, st, s, e, km = best
    return {"step_id": st.id, "step_code": st.code, "step_name": st.name, "start": s, "end": e,
            "site_id": st.site_id, "km": km}


def _expire_offers(world: World) -> None:
    from app.sync_engine import open_gaps
    live = {g.id for g in open_gaps(world)}
    for o in world.offers.values():
        if o.status == "OPEN" and (o.gap_id not in live or TODAY > o.start - 1):
            o.status = "EXPIRED"


def publish_offer(world: World, user: User, gap_id: str) -> Offer:
    from app.sync_engine import open_gaps
    _require_pm(user)
    gap = next((g for g in open_gaps(world) if g.id == gap_id), None)
    if gap is None:
        raise ValueError("gap no longer open")
    if gap.type != "SURPLUS":
        raise ValueError("only idle (surplus) capacity can be offered")
    if world.sites[gap.site_id].org_id != user.org_id:
        raise PermissionError("not your site")
    for o in world.offers.values():
        if o.gap_id == gap_id and o.status in LIVE_OFFER + ("TAKEN",):
            return o
    offer = Offer(world.next_id("offer"), gap_id, user.org_id, gap.site_id, gap.crew_id, gap.step_id, gap.trade,
                  gap.workers, gap.start, gap.end, world.sites[gap.site_id].area, created_at=world.now())
    world.offers[offer.id] = offer
    world.log("OfferPublished", user.id, gap.site_id, {"offer_id": offer.id})
    for org in {s.org_id for s in world.sites.values() if s.org_id != user.org_id}:
        fit = offer_fit(world, offer, org)
        if fit:
            world.notify(world.pms_of(org),
                         f"{trade_label(offer.trade)} crew available near you: {offer.workers} workers, days "
                         f"{offer.start}–{offer.end} · fits your {world.steps[fit['step_id']].site_id}-"
                         f"{fit['step_code']} {short_name(fit['step_name'])} (from {anon_label(offer.site_id)})",
                         offer.id)
    return offer


def withdraw_offer(world: World, user: User, offer_id: str) -> Offer:
    o = world.offers.get(offer_id)
    if o is None:
        raise ValueError(f"unknown offer {offer_id}")
    if o.org_id != user.org_id:
        raise PermissionError("not your offer")
    if o.status not in LIVE_OFFER:
        raise ValueError(f"offer already {o.status.lower()}")
    o.status = "WITHDRAWN"
    world.log("OfferWithdrawn", user.id, o.site_id, {"offer_id": o.id})
    return o


# ---------------------------------------------------------------- view grants
def request_view(world: World, user: User, anon: str) -> ViewGrant:
    _require_pm(user)
    sid = site_for_anon(world, anon)
    owner = world.sites[sid].org_id
    if owner == user.org_id:
        raise ValueError("that's your own project")
    for g in world.view_grants.values():
        if g.site_id == sid and g.viewer_org == user.org_id and g.status in ("REQUESTED", "GRANTED"):
            return g
    g = ViewGrant(world.next_id("view"), sid, owner, user.org_id, user.id, created_at=world.now())
    world.view_grants[g.id] = g
    world.log("ViewRequested", user.id, None, {"view_id": g.id, "_org": user.org_id})
    world.notify(world.pms_of(owner), f"{world.orgs[user.org_id].name} asks to see {world.sites[sid].name}, "
                                      "anonymised.", g.id)
    return g


def decide_view(world: World, user: User, view_id: str, share: bool) -> ViewGrant:
    g = world.view_grants.get(view_id)
    if g is None:
        raise ValueError(f"unknown view request {view_id}")
    _require_pm(user)
    if user.org_id != g.owner_org:
        raise PermissionError("only the project's company can decide")
    if g.status != "REQUESTED":
        raise ValueError(f"view request already {g.status.lower()}")
    g.status = "GRANTED" if share else "DECLINED"
    g.decided_at = world.now()
    world.log("ViewGranted" if share else "ViewDeclined", user.id, g.site_id, {"view_id": g.id})
    world.notify(g.requested_by, f"{anon_company(g.site_id)} {'shared' if share else 'declined'} an anonymised "
                                 f"view of {anon_label(g.site_id)}.", g.id)
    return g


def view_granted(world: World, site_id: str, org_id: str) -> bool:
    return any(g.site_id == site_id and g.viewer_org == org_id and g.status == "GRANTED"
               for g in world.view_grants.values())


# ---------------------------------------------------------------- links (crew requests)
def request_link(world: World, user: User, offer_id: str, purpose: str) -> Link:
    _require_pm(user)
    o = world.offers.get(offer_id)
    if o is None:
        raise ValueError(f"unknown offer {offer_id}")
    if o.org_id == user.org_id:
        raise ValueError("cannot request your own offer")
    if o.status != "OPEN":
        raise ValueError(f"offer is {o.status.lower()}")
    fit = offer_fit(world, o, user.org_id)
    if not fit:
        raise ValueError("this offer doesn't fit any of your sites")
    link = Link(world.next_id("link"), user.org_id, o.org_id, user.id, purpose, offer_id=o.id,
                target_step_id=fit["step_id"], created_at=world.now())
    world.links[link.id] = link
    o.status = "REQUESTED"
    world.log("LinkRequested", user.id, None, {"link_id": link.id, "offer_id": o.id, "_org": user.org_id})
    world.notify(world.pms_of(o.org_id), f"{world.orgs[user.org_id].name} requests your offered "
                                         f"{trade_label(o.trade)} crew (days {o.start}–{o.end}) for their "
                                         f"{short_name(fit['step_name'])}.", link.id)
    return link


def decide_link(world: World, user: User, link_id: str, accept: bool, pool_terms: dict | None = None) -> Link:
    link = world.links.get(link_id)
    if link is None:
        raise ValueError(f"unknown link {link_id}")
    _require_pm(user)
    if user.org_id != link.org_b:
        raise PermissionError("only the offering company's PM can decide")
    if link.status != "REQUESTED":
        raise ValueError(f"request already {link.status.lower()}")
    offer = world.offers.get(link.offer_id) if link.offer_id else None
    link.decided_at = world.now()
    if not accept:
        link.status = "DECLINED"
        if offer:
            offer.status = "OPEN"
        world.log("LinkDeclined", user.id, None, {"link_id": link_id})
        world.notify(link.requested_by, f"{anon_company(offer.site_id) if offer else 'The other company'} declined "
                                        "your crew request.", link_id)
        return link
    link.status = "ACTIVE"
    link.pool = {**DEFAULT_POOL, **(pool_terms or {})}
    world.log("LinkAccepted", user.id, None, {"link_id": link_id, "pool": link.pool})
    if offer:
        offer.status = "TAKEN"
        from app.sync_engine import approve_option
        res = approve_option(world, user, offer.gap_id, "M8", target_step_id=link.target_step_id)
        cp = world.cross_proposals[res["cross_proposal_id"]]
        cp["accepted"][link.org_a] = True  # the borrower asked for the crew: its acceptance is the request
        cp["link_id"] = link.id
        home = world.sites[offer.site_id]
        world.notify(link.requested_by, f"{world.orgs[user.org_id].name} accepted: {offer.workers} workers, days "
                                        f"{offer.start}–{offer.end}, back on {home.name} by day {offer.end}. "
                                        "Waiting for the subcontractor.", link_id)
        world.notify(world.users_of(cp["sub_org"]),
                     f"New proposal: move {world.crews[cp['crew_id']].name} to {world.orgs[link.org_a].name}, "
                     f"days {cp['start']}–{cp['end']}, back by day {cp['end']}.", cp["id"])
    return link


# ---------------------------------------------------------------- cross-proposals
def send_cross_proposal(world: World, user: User, gap, opt, target_step_id: str | None = None) -> dict:
    from app.schedule import forward_pass, site_finish
    from app.config import RETURN_LAG_DAYS
    target_step_id = target_step_id or opt.target_step_id
    home_start = forward_pass(world, gap.site_id, "confirmed")[gap.step_id][0]
    no_action = site_finish(forward_pass(world, gap.site_id, "confirmed",
                                         min_start={gap.step_id: home_start + RETURN_LAG_DAYS}))
    cause = _latest_cause(world, gap.site_id)
    cp = {"id": world.next_id("cp"), "option_id": opt.id, "gap_id": gap.id, "from_org": user.org_id,
          "to_org": world.sites[world.steps[target_step_id].site_id].org_id,
          "sub_org": world.crews[gap.crew_id].org_id, "crew_id": gap.crew_id, "home_step_id": gap.step_id,
          "target_step_id": target_step_id, "start": gap.start, "end": gap.end, "accepted": {}, "status": "SENT",
          "created_at": world.now(), "days_protected": opt.days_protected,
          "value_gbp": opt.days_protected * world.sites[gap.site_id].day_value,
          "idle_cost_avoided_gbp": opt.idle_cost_avoided_gbp, "no_action_finish": no_action,
          "event": cause["event"], "evidence": cause["evidence"]}
    world.cross_proposals[cp["id"]] = cp
    world.log("ProposalSent", user.id, gap.site_id, {"cross_proposal_id": cp["id"]})
    return cp


def _latest_cause(world: World, site_id: str) -> dict:
    applied = [p for p in world.proposals.values()
               if p["site_id"] == site_id and p["status"] == "APPLIED" and p.get("changes")]
    if not applied:
        return {"event": f"{world.sites[site_id].name}: schedule change", "evidence": "forecast snapshot"}
    p = applied[-1]
    c = next((c for c in p["changes"] if c["field"] == "delay_days"), p["changes"][0])
    st = world.steps[c["step_id"]]
    days = c["to"] - c.get("from", 0)
    reason = p["source"].get("reason") or "update"
    kind = {"voice": "Plaud note", "typed": "typed update", "timeline": "timeline edit"}.get(p["source"].get("kind"),
                                                                                             "update")
    return {"event": f"{world.sites[site_id].name}: {st.code} {st.name} +{days} ({reason})",
            "evidence": f"{kind} · forecast snapshot v{world.versions[site_id]} · acceptances"}


def decide_cross_proposal(world: World, user: User, cp_id: str, accept: bool) -> dict:
    cp = world.cross_proposals.get(cp_id)
    if cp is None:
        raise ValueError(f"unknown proposal {cp_id}")
    if user.org_id not in (cp["to_org"], cp["sub_org"]):
        raise PermissionError("not a party to this proposal")
    if cp["status"] in ("AGREED", "DECLINED", "DONE"):
        raise ValueError(f"proposal already {cp['status'].lower()}")
    cp["accepted"][user.org_id] = accept
    cp.setdefault("decided_at", {})[user.org_id] = world.now()
    world.log("ProposalAccepted" if accept else "ProposalDeclined", user.id, None,
              {"cross_proposal_id": cp_id, "_org": user.org_id})
    if not accept:
        cp["status"] = "DECLINED"
        world.option_states[cp["option_id"]] = "FAILED"
        world.notify(world.pms_of(cp["from_org"]) + world.pms_of(cp["to_org"]),
                     f"{world.orgs[user.org_id].name} declined the crew move.", cp_id)
        return {"status": "DECLINED", "proposals": []}
    if all(cp["accepted"].get(o) for o in (cp["to_org"], cp["sub_org"])):
        cp["status"] = "AGREED"
        from app.proposals import booking_proposal
        p1 = booking_proposal(world, cp, org_id=cp["to_org"], kind="add_swap_booking")
        p2 = booking_proposal(world, cp, org_id=cp["from_org"], kind="confirm_return")
        world.notify(world.pms_of(cp["to_org"]), f"{world.orgs[cp['sub_org']].name} accepted the move. "
                                                 "Confirm the booking on your site.", p1["id"])
        world.notify(world.pms_of(cp["from_org"]), f"{world.orgs[cp['sub_org']].name} accepted the move. "
                                                   "Your booking change is ready once the other company confirms.",
                     p2["id"])
        return {"status": "AGREED", "proposals": [p1, p2]}
    cp["status"] = "PARTIAL"
    return {"status": "PARTIAL", "proposals": []}


# ---------------------------------------------------------------- labels
TRADE_LABELS = {"mep": "M&E", "rc_frame": "RC frame", "ground_investigation": "Ground investigation"}


def trade_label(trade: str) -> str:
    return TRADE_LABELS.get(trade, trade.replace("_", " ").capitalize())


def short_name(step_name: str) -> str:
    """'MEP first fix (pipes, cables, ducts), lower floors' -> 'first fix'."""
    s = step_name.split("(")[0].split(",")[0].strip()
    if s.startswith("MEP "):
        s = s[4:]
    return s[:1].lower() + s[1:] if s and not (len(s) > 1 and s[1].isupper()) else s
