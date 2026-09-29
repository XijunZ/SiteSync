from graphlib import TopologicalSorter

from app.domain import World


def _site_steps(world: World, site_id: str) -> dict:
    return {s.id: s for s in world.steps.values() if s.site_id == site_id}


def forward_pass(world: World, site_id: str, mode: str = "confirmed",
                 min_start: dict[str, int] | None = None) -> dict[str, tuple[int, int]]:
    steps = _site_steps(world, site_id)
    offset = world.sites[site_id].offset
    order = TopologicalSorter({sid: st.deps for sid, st in steps.items()}).static_order()
    out: dict[str, tuple[int, int]] = {}
    for sid in order:
        st = steps[sid]
        start = max([offset] + [out[d][1] for d in st.deps])
        if mode in ("confirmed", "risk"):
            start += st.lag_days
        if min_start and sid in min_start:
            start = max(start, min_start[sid])
        extra = 0
        if mode in ("confirmed", "risk"):
            extra += st.delay_days
        if mode == "risk":
            extra += st.risk_days
        out[sid] = (start, start + st.days + extra)
    return out


def natural_start(world: World, site_id: str, step_id: str, mode: str = "confirmed") -> int:
    """Earliest start from predecessors (before this step's own lag)."""
    st = world.steps[step_id]
    dates = forward_pass(world, site_id, mode)
    return max([world.sites[site_id].offset] + [dates[d][1] for d in st.deps])


def site_finish(dates: dict[str, tuple[int, int]]) -> int:
    return max(end for _, end in dates.values())


def critical_steps(world: World, site_id: str, dates: dict[str, tuple[int, int]]) -> set[str]:
    steps = _site_steps(world, site_id)
    succ: dict[str, list[str]] = {sid: [] for sid in steps}
    for st in steps.values():
        for d in st.deps:
            succ[d].append(st.id)
    finish = site_finish(dates)
    latest_end: dict[str, int] = {}
    order = list(TopologicalSorter({sid: st.deps for sid, st in steps.items()}).static_order())
    for sid in reversed(order):
        if not succ[sid]:
            latest_end[sid] = finish
        else:
            latest_end[sid] = min(latest_end[s] - (dates[s][1] - dates[s][0]) for s in succ[sid])
    return {sid for sid in steps if latest_end[sid] == dates[sid][1]}


def all_dates(world: World, mode: str = "confirmed") -> dict[str, dict[str, tuple[int, int]]]:
    return {sid: forward_pass(world, sid, mode) for sid in world.sites}
