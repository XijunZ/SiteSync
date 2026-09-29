from collections import defaultdict
from dataclasses import dataclass

from app.config import LOOKAHEAD_DAYS, TODAY
from app.domain import Booking, World


@dataclass(frozen=True)
class Imbalance:
    type: str  # SURPLUS | SHORTAGE | CLASH
    site_id: str
    step_id: str
    crew_id: str | None
    trade: str
    start: int
    end: int
    workers: int


def effective_booking_end(world: World, b: Booking) -> int:
    """A delayed step's own booking is assumed extended by the delay (spec §5.2)."""
    return b.end + world.steps[b.step_id].delay_days


def _runs(days: list[int]) -> list[tuple[int, int]]:
    runs, start, prev = [], None, None
    for d in sorted(days):
        if start is None:
            start = prev = d
        elif d == prev + 1:
            prev = d
        else:
            runs.append((start, prev + 1))
            start = prev = d
    if start is not None:
        runs.append((start, prev + 1))
    return runs


def _active(dates_by_site, world: World, step_id: str, day: int) -> bool:
    s, e = dates_by_site[world.steps[step_id].site_id][step_id]
    return s <= day < e


def imbalances(world: World, dates_by_site: dict, window: tuple[int, int] | None = None) -> list[Imbalance]:
    lo, hi = window or (TODAY, TODAY + LOOKAHEAD_DAYS)
    out: list[Imbalance] = []
    by_crew: dict[str, list[Booking]] = defaultdict(list)
    for b in world.bookings.values():
        by_crew[b.crew_id].append(b)
    for crew_id, bookings in by_crew.items():
        crew = world.crews[crew_id]
        surplus: dict[str, list[int]] = defaultdict(list)
        clash: dict[str, list[int]] = defaultdict(list)
        for day in range(lo, hi):
            covering = [b for b in bookings if b.start <= day < effective_booking_end(world, b)]
            if not covering:
                continue
            productive = [b for b in covering if _active(dates_by_site, world, b.step_id, day)]
            if not productive:
                surplus[covering[0].step_id].append(day)
            elif len({world.steps[b.step_id].site_id for b in productive}) > 1:
                clash[productive[0].step_id].append(day)
        for step_id, days in surplus.items():
            st = world.steps[step_id]
            out += [Imbalance("SURPLUS", st.site_id, step_id, crew_id, crew.trade, s, e, crew.size)
                    for s, e in _runs(days)]
        for step_id, days in clash.items():
            st = world.steps[step_id]
            out += [Imbalance("CLASH", st.site_id, step_id, crew_id, crew.trade, s, e, crew.size)
                    for s, e in _runs(days)]
    for st in world.steps.values():
        if not (st.has_crew and st.headcount):
            continue
        s, e = dates_by_site[st.site_id][st.id]
        own = [b for b in world.bookings.values() if b.step_id == st.id]
        short: dict[int, list[int]] = defaultdict(list)  # workers short -> days
        for d in range(max(s, lo), min(e, hi)):
            booked = sum(world.crews[b.crew_id].size for b in own if b.start <= d < effective_booking_end(world, b))
            if booked < st.headcount:
                short[st.headcount - booked].append(d)
        for workers, days in short.items():
            out += [Imbalance("SHORTAGE", st.site_id, st.id, None, st.trade, a, z, workers) for a, z in _runs(days)]
    return sorted(out, key=lambda i: (i.start, i.site_id, i.step_id, i.type))


def diff_imbalances(before: list[Imbalance], after: list[Imbalance]) -> dict:
    b, a = set(before), set(after)
    return {"created": [i for i in after if i not in b], "resolved": [i for i in before if i not in a]}
