"""Graph explanations shown in the UI: the ripple chain of a change and how a slot-swap partner was found.

Answered by Cypher on the Neo4j mirror when STORE=neo4j; otherwise (or if Aura fails) the same shape is
computed from the in-memory world with `source: "memory"`, so the UI never breaks.
"""
import time

from app.config import MAX_SWAP_KM
from app.domain import User, World
from app.graph_neo4j import AFFECTED_CYPHER, RIPPLE_CYPHER, SWAP_CYPHER, get_mirror
from app.network import anon_company, anon_label
from app.schedule import forward_pass
from app.schedule import all_dates
from app.sync_engine import _overlap_ok, link_active, open_gaps, swap_candidates_memory

HANDOVER_CODE = "L7"
GRAPH_LOG: list[dict] = []


def _log(name: str, ms: float, source: str) -> None:
    GRAPH_LOG.append({"name": name, "ms": ms, "source": source, "at": time.strftime("%H:%M:%S")})
    del GRAPH_LOG[:-20]


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000, 1)


def _ripple_memory(world: World, start_id: str, end_id: str) -> dict:
    site = world.steps[start_id].site_id
    dates = forward_pass(world, site, "confirmed")
    succ: dict[str, list[str]] = {sid: [] for sid in dates}
    for st in world.steps.values():
        if st.site_id == site:
            for d in st.deps:
                succ[d].append(st.id)

    def node(sid):
        st = world.steps[sid]
        return {"code": st.code, "name": st.name, "conf_start": dates[sid][0], "conf_end": dates[sid][1]}

    def longest(sid, tight):
        if sid == end_id:
            return [sid]
        best = None
        for nxt in succ[sid]:
            if tight and dates[nxt][0] != dates[sid][1]:
                continue
            tail = longest(nxt, tight)
            if tail and (best is None or len(tail) > len(best)):
                best = tail
        return [sid] + best if best else None

    chain = longest(start_id, True) or longest(start_id, False) or []
    seen, stack = set(), [start_id]
    while stack:
        for nxt in succ[stack.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return {"path": [node(s) for s in chain], "hops": max(len(chain) - 1, 0), "affected_count": len(seen)}


def ripple(world: World, site_id: str, step_code: str) -> dict:
    start_id, end_id = f"{site_id}-{step_code}", f"{site_id}-{HANDOVER_CODE}"
    if start_id not in world.steps:
        raise ValueError(f"unknown step {step_code}")
    cypher = RIPPLE_CYPHER + "\n\n// downstream steps\n" + AFFECTED_CYPHER
    t0 = time.perf_counter()
    mirror = get_mirror()
    if mirror:
        try:
            r = mirror.ripple(start_id, end_id)
            ms = _ms(t0); _log("ripple (DEPENDS_ON path)", ms, "neo4j")
            return {**r, "cypher": cypher, "ms": ms, "source": "neo4j"}
        except Exception:  # noqa: BLE001 - fall back to the in-memory answer
            t0 = time.perf_counter()
    r = _ripple_memory(world, start_id, end_id)
    ms = _ms(t0); _log("ripple (DEPENDS_ON path)", ms, "memory")
    return {**r, "cypher": cypher, "ms": ms, "source": "memory"}


def swap_explain(world: World, user: User, gap_id: str) -> dict:
    gap = next((g for g in open_gaps(world) if g.id == gap_id), None)
    if gap is None:
        raise KeyError(gap_id)
    home_org = world.sites[gap.site_id].org_id
    crew = world.crews[gap.crew_id]
    sub_org = crew.org_id
    t0 = time.perf_counter()
    rows, source, pattern_matches = None, "memory", 0
    mirror = get_mirror()
    if mirror:
        try:
            raw = mirror.swap_candidates(sub_org, gap.site_id, gap.trade, MAX_SWAP_KM)
            pattern_matches = len(raw)
            dates = all_dates(world)
            rows = [(r["step_id"], r["crew_id"], r["km"]) for r in raw if _overlap_ok(world, dates, gap, r["step_id"])]
            source = "neo4j"
        except Exception:  # noqa: BLE001
            rows = None
    if rows is None:
        t0 = time.perf_counter()
        rows = swap_candidates_memory(world, gap)
        pattern_matches = len(rows)
    ms = _ms(t0)
    _log("swap match (EMPLOYS/APPROVED_AT + point.distance)", ms, source)
    out = []
    for step_id, crew_id, km in rows:
        st = world.steps[step_id]
        target_org = world.sites[st.site_id].org_id
        if user.org_id != home_org and user.org_id != target_org:
            continue  # only the two parties of this match see it
        revealed = user.org_id == target_org or link_active(world, user.org_id, target_org)
        out.append({"sub": world.orgs[sub_org].name, "crew": world.crews[crew_id].name,
                    "target_site": world.sites[st.site_id].name if revealed else anon_label(st.site_id),
                    "step_code": st.code if revealed else None, "trade": st.trade,
                    "km": round(km, 2), "approved_at_gc": world.orgs[target_org].name if revealed
                    else anon_company(st.site_id)})
    return {"gap_id": gap_id, "sub": world.orgs[sub_org].name, "idle_crew": crew.name,
            "home_site": world.sites[gap.site_id].name if user.org_id == home_org else anon_label(gap.site_id),
            "rows": out, "pattern_matches": pattern_matches, "window": [gap.start, gap.end], "cypher": SWAP_CYPHER, "ms": ms, "source": source, "max_km": MAX_SWAP_KM}


def stats(world: World) -> dict:
    mirror = get_mirror()
    if mirror:
        try:
            t0 = time.perf_counter()
            r = mirror.stats()
            _log("graph stats (count nodes/rels)", _ms(t0), "neo4j")
            return {**r, "source": "neo4j"}
        except Exception:  # noqa: BLE001
            pass
    steps = list(world.steps.values())
    nodes = len(world.orgs) + len(world.sites) + len(steps) + len(world.crews) + len(world.bookings)
    rels = (len(world.sites) + len(steps) + sum(len(s.deps) for s in steps) + len(world.crews)
            + 2 * len(world.bookings) + len(world.approvals))
    return {"nodes": nodes, "relationships": rels, "source": "memory"}


def check_swap_viewer(world: World, user: User, gap_id: str) -> None:
    """Lender PMs of the gap's site, or the borrower once linked, may see the explanation."""
    gap = next((g for g in open_gaps(world) if g.id == gap_id), None)
    if gap is None:
        raise KeyError(gap_id)
    home_org = world.sites[gap.site_id].org_id
    if user.org_id == home_org:
        return
    if link_active(world, user.org_id, home_org):
        return
    raise PermissionError("not a party to this match")

