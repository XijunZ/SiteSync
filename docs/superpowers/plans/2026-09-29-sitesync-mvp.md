# SiteSync MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the SiteSync demo: a dependency-graph timeline for 4 sites across 2 GCs, where a voice note (Plaud) proposes a delay, the knock-on in dates and labour is shown before confirming, the Sync Board ranks site-sync mechanisms with deadlines, and a slot swap between two GCs is completed through link, pool and cross-company proposals.

**Architecture:** An in-memory `World` (dataclasses) is the engine's working state; pure functions compute schedules, labour balance, gaps and options from it. Every change is an event. Neo4j Aura mirrors the world and runs the graph-native queries (Cypher propagation with parity to the Python engine, slot-swap candidate search with `point.distance`). FastAPI serves a role-scoped API (header `X-User-Id`) to a single static HTML page.

**Tech Stack:** Python 3.11, uv, FastAPI, pydantic v2, neo4j driver 6.x, openai SDK (Crusoe / OpenRouter), httpx, pytest; vanilla JS + SVG front end.

**Spec:** `docs/02-technical-spec.md` (v2) and `docs/01-product-requirements.md` (v2, MVP = §7).

## Global Constraints

- Python `>=3.11,<3.12`; run everything with `uv run`.
- Integer working days on one global axis; `end` is exclusive; `TODAY = 220`; lookahead `[220, 240)`.
- Programme = CSV rows with ids starting F, G, H, J, K, L (52 steps); drop dependencies outside that set; **add K3 → J6**.
- Sites: A (Northgate, offset 12), B (Northgate, 100), C (Riverside, 7), D (Riverside, 185); coordinates as in spec §4.
- `RETURN_LAG_DAYS = 3`, `CREW_DAY_GBP = 1200`, `MAX_SWAP_KM = 10`, PM approval threshold: finish date moves, or a critical step slips ≥ 2 days.
- Every API response is built by `app/views.py`; no other org's site names, site ids, step ids or user names may appear unless a link is ACTIVE (org name only) or a cross-proposal was accepted by both sides.
- LLM providers from `LLM_PROVIDERS` (default `crusoe,openrouter`); the deterministic extractor is the last fallback, so the demo never depends on an external API.
- Never commit `.env`. Commit after every task.

## Review Focus

1. **Transcript with no recognisable step or no delay** (chatter, "all good today") → returns no proposal and a clear message, never a guessed change. Test in Task 7.
2. **Delay expressed in words** ("a week", "couple of days", "five days") → 5, 2, 5. Test in Task 7.
3. **Deciding a proposal twice, or after the site's version moved on** → 409 with `{error: "stale"}`. Test in Task 8.
4. **Demo reset mid-flow** → links, proposals, cross-proposals, events all cleared; state equals fresh seed. Test in Task 10.
5. **Missing or unknown `X-User-Id`** → 401 `{error: "unknown_user"}`. Test in Task 10.

## File Structure

```
app/
  config.py        constants, env
  domain.py        dataclasses: Org, User, Site, Step, Crew, Booking, Approval, Link, World
  schedule.py      forward pass (baseline/confirmed/risk), finish, critical steps
  labour.py        Imbalance, imbalances(), diff_imbalances()
  sync_engine.py   Gap, Option, open_gaps(), options_for(), approve_option()
  network.py       links, pools, cross-proposals
  proposals.py     Proposal, build_proposal(), decide_proposal()
  vocab.py         step synonyms, words→numbers, deterministic extractor
  llm.py           provider chain (Crusoe → OpenRouter), JSON extraction, call log
  ingest.py        text → ExtractedUpdate list (LLM, then deterministic fallback)
  plaud.py         Plaud CLI wrapper + transcript parser
  signals.py       risk flags, Open-Meteo refresh
  views.py         scopes, anonymisation, response builders
  graph_neo4j.py   Neo4j mirror, Cypher propagation, slot-swap candidates
  main.py          FastAPI routes
seed/
  programme.py     CSV → step templates (trade map, headcount)
  seed.py          build_world()
static/index.html  UI
scripts/dump_fixtures.py
tests/ ...
```

---

### Task 1: Programme loader and world seed

**Files:**
- Create: `app/config.py`, `app/domain.py`, `seed/__init__.py`, `seed/programme.py`, `seed/seed.py`
- Test: `tests/test_seed.py`

**Interfaces:**
- Produces: `load_programme() -> list[dict]` (keys: code, phase, name, trade, has_crew, days, deps, weather_sensitive, kind, risk_note, headcount); `build_world() -> World`; dataclasses in `app/domain.py` exactly as below.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_seed.py
from seed.programme import load_programme
from seed.seed import build_world

def test_programme_has_52_on_site_steps_with_k3_j6():
    steps = load_programme()
    assert len(steps) == 52
    k3 = next(s for s in steps if s["code"] == "K3")
    assert "J6" in k3["deps"] and "K1" in k3["deps"]
    assert all(d[0] in "FGHJKL" for s in steps for d in s["deps"])

def test_world_shape():
    w = build_world()
    assert set(w.sites) == {"A", "B", "C", "D"}
    assert len(w.steps) == 4 * 52
    assert w.sites["A"].org_id == "NG" and w.sites["C"].org_id == "RV"
    assert w.steps["A-K3"].headcount == 6
    s1 = [b for b in w.bookings.values() if b.crew_id == "SPARKS-S1"]
    assert any(b.step_id == "A-K3" and (b.start, b.end) == (230, 250) for b in s1)
    s2 = [b for b in w.bookings.values() if b.crew_id == "SPARKS-S2"]
    assert any(b.step_id == "C-K3" and (b.start, b.end) == (225, 245) for b in s2)
    assert any(b.step_id == "A-K5" and b.crew_id.startswith("VOLT") for b in w.bookings.values())
    assert {(a.sub_org_id, a.gc_org_id) for a in w.approvals} >= {("SPARKS", "NG"), ("SPARKS", "RV")}
    assert set(w.users) == {"dan", "priya", "marcus", "sam", "ops"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_seed.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'seed.programme'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

TODAY = 220
LOOKAHEAD_DAYS = 20
RETURN_LAG_DAYS = 3
CREW_DAY_GBP = 1200
MAX_SWAP_KM = 10.0
PM_CRITICAL_SLIP_DAYS = 2
STORE = os.getenv("STORE", "memory")
LLM_PROVIDERS = [p.strip() for p in os.getenv("LLM_PROVIDERS", "crusoe,openrouter").split(",") if p.strip()]
```

```python
# app/domain.py
from dataclasses import dataclass, field


@dataclass
class Org:
    id: str
    name: str
    type: str  # GC | SUB | AGENCY


@dataclass
class User:
    id: str
    name: str
    role: str  # SITE_MANAGER | PM | OPS_DIRECTOR | SUB_PLANNER | OPERATOR
    org_id: str
    site_ids: list[str]


@dataclass
class Site:
    id: str
    name: str
    org_id: str
    lat: float
    lon: float
    offset: int
    day_value: int
    area: str
    publish: bool = True
    confidential: bool = False


@dataclass
class Step:
    id: str
    site_id: str
    code: str
    phase: str
    name: str
    trade: str
    has_crew: bool
    kind: str
    days: int
    deps: list[str]
    weather_sensitive: bool
    risk_note: str | None
    headcount: int
    delay_days: int = 0
    risk_days: int = 0


@dataclass
class Crew:
    id: str
    org_id: str
    trade: str
    size: int
    name: str


@dataclass
class Booking:
    id: str
    crew_id: str
    step_id: str
    start: int
    end: int
    source: str = "seed"


@dataclass
class Approval:
    sub_org_id: str
    gc_org_id: str
    setup_days: int = 0


@dataclass
class Link:
    id: str
    org_a: str
    org_b: str
    requested_by: str
    purpose: str
    status: str = "REQUESTED"  # REQUESTED | ACTIVE | DECLINED
    pool: dict | None = None


@dataclass
class World:
    orgs: dict[str, Org] = field(default_factory=dict)
    users: dict[str, User] = field(default_factory=dict)
    sites: dict[str, Site] = field(default_factory=dict)
    steps: dict[str, Step] = field(default_factory=dict)
    crews: dict[str, Crew] = field(default_factory=dict)
    bookings: dict[str, Booking] = field(default_factory=dict)
    approvals: list[Approval] = field(default_factory=list)
    links: dict[str, Link] = field(default_factory=dict)
    proposals: dict = field(default_factory=dict)
    cross_proposals: dict = field(default_factory=dict)
    option_states: dict = field(default_factory=dict)
    outcomes: list = field(default_factory=list)
    events: list = field(default_factory=list)
    versions: dict[str, int] = field(default_factory=dict)
    snapshots: list = field(default_factory=list)
    seq: int = 0

    def next_id(self, prefix: str) -> str:
        self.seq += 1
        return f"{prefix}-{self.seq}"

    def log(self, type_: str, user_id: str | None, site_id: str | None, payload: dict, source: dict | None = None) -> dict:
        ev = {"id": self.next_id("ev"), "type": type_, "user_id": user_id, "site_id": site_id,
              "payload": payload, "source": source or {"kind": "system"},
              "version": self.versions.get(site_id) if site_id else None}
        self.events.append(ev)
        return ev
```

```python
# seed/__init__.py
```

```python
# seed/programme.py
import csv
from pathlib import Path

CSV_PATH = Path(__file__).parent / "development_programme_seed.csv"
ON_SITE = tuple("FGHJKL")
EXTRA_DEPS = {"K3": ["J6"]}  # M&E first fix needs the building weathertight (spec §4)

TRADE_MAP: dict[str, tuple[str, bool]] = {
    "Surveyor": ("surveyor", False), "Council": ("council", False),
    "Utility companies": ("utilities", False), "Milestone": ("milestone", False),
    "Building control": ("building_control", False), "General contractor": ("general_contractor", False),
    "Developer": ("developer", False),
    "Groundworks": ("groundworks", True), "Groundworks, concrete": ("groundworks", True),
    "Concrete": ("concrete", True), "Demolition": ("demolition", True),
    "Demolition, haulage": ("demolition", True), "Licensed asbestos contractor": ("asbestos", True),
    "Specialist contractor": ("ground_investigation", True), "Piling contractor": ("piling", True),
    "RC frame": ("rc_frame", True), "Roofing": ("roofing", True), "Glazing": ("glazing", True),
    "Cladding": ("cladding", True), "Scaffolding": ("scaffolding", True),
    "Bricklaying": ("bricklaying", True), "Mechanical and electrical": ("mep", True),
    "Drylining": ("drylining", True), "Fit-out carpentry": ("carpentry", True),
    "Painting, flooring": ("finishes", True), "Lift contractor": ("lifts", True),
    "Landscaping": ("landscaping", True),
}

HEADCOUNT = {"demolition": 6, "groundworks": 6, "concrete": 5, "piling": 4, "rc_frame": 8,
             "roofing": 4, "glazing": 4, "cladding": 5, "scaffolding": 4, "bricklaying": 5,
             "mep": 6, "drylining": 5, "carpentry": 4, "finishes": 4, "lifts": 3,
             "landscaping": 4, "asbestos": 4, "ground_investigation": 3}


def load_programme(path: Path = CSV_PATH) -> list[dict]:
    with open(path, newline="") as f:
        rows = [r for r in csv.DictReader(f) if r["id"].startswith(ON_SITE)]
    ids = {r["id"] for r in rows}
    out = []
    for r in rows:
        raw = r["owner_or_trade"]
        if raw not in TRADE_MAP:
            raise ValueError(f"unknown trade {raw!r} on step {r['id']}")
        trade, has_crew = TRADE_MAP[raw]
        deps = [d for d in r["depends_on"].split(";") if d in ids] + EXTRA_DEPS.get(r["id"], [])
        out.append({
            "code": r["id"], "phase": r["phase"], "name": r["name"], "trade": trade,
            "has_crew": has_crew, "days": int(r["duration_working_days"]), "deps": deps,
            "weather_sensitive": r["weather_sensitive"] == "1", "kind": r["kind"],
            "risk_note": r["delay_risk"] or None,
            "headcount": HEADCOUNT.get(trade, 0) if has_crew else 0,
        })
    return out
```

```python
# seed/seed.py
from app.domain import Approval, Booking, Crew, Org, Site, Step, User, World
from app.schedule import forward_pass
from seed.programme import load_programme

SITES = [
    ("A", "Hackney Wick Yard", "NG", 51.5433, -0.0243, 12),
    ("B", "Stratford Mill", "NG", 51.5417, -0.0036, 100),
    ("C", "Bow Wharf", "RV", 51.5282, -0.0183, 7),
    ("D", "Canning Town Works", "RV", 51.5147, 0.0080, 185),
]
DAY_VALUE = 8000  # £ per site per day of delay (demo assumption, shown on screen)
SPARKS_CREW_BY_SITE = {"A": "SPARKS-S1", "C": "SPARKS-S2"}


def build_world() -> World:
    w = World()
    for org in [Org("NG", "Northgate Build", "GC"), Org("RV", "Riverside Construction", "GC"),
                Org("SPARKS", "Sparks Electrical", "SUB"), Org("VOLT", "Voltline M&E", "SUB"),
                Org("CREWNOW", "CrewNow Agency", "AGENCY")]:
        w.orgs[org.id] = org
    for u in [User("dan", "Dan", "SITE_MANAGER", "NG", ["A"]), User("priya", "Priya", "PM", "NG", ["A", "B"]),
              User("marcus", "Marcus", "PM", "RV", ["C", "D"]), User("sam", "Sam", "SUB_PLANNER", "SPARKS", []),
              User("ops", "SiteSync operator", "OPERATOR", "SITESYNC", [])]:
        w.users[u.id] = u
    templates = load_programme()
    for sid, name, org, lat, lon, off in SITES:
        w.sites[sid] = Site(sid, name, org, lat, lon, off, DAY_VALUE, area="East London")
        w.versions[sid] = 0
        for t in templates:
            w.steps[f"{sid}-{t['code']}"] = Step(
                id=f"{sid}-{t['code']}", site_id=sid, code=t["code"], phase=t["phase"], name=t["name"],
                trade=t["trade"], has_crew=t["has_crew"], kind=t["kind"], days=t["days"],
                deps=[f"{sid}-{d}" for d in t["deps"]], weather_sensitive=t["weather_sensitive"],
                risk_note=t["risk_note"], headcount=t["headcount"])
    for cid, org, name in [("SPARKS-S1", "SPARKS", "Sparks crew 1"), ("SPARKS-S2", "SPARKS", "Sparks crew 2")]:
        w.crews[cid] = Crew(cid, org, "mep", 6, name)
    w.approvals += [Approval("SPARKS", "NG"), Approval("SPARKS", "RV"), Approval("VOLT", "NG"),
                    Approval("VOLT", "RV"), Approval("CREWNOW", "NG", setup_days=1)]
    for sid in w.sites:
        base = forward_pass(w, sid, "baseline")
        for st in [s for s in w.steps.values() if s.site_id == sid and s.has_crew and s.headcount]:
            crew_id = _crew_for(w, st)
            start, end = base[st.id]
            bid = w.next_id("bk")
            w.bookings[bid] = Booking(bid, crew_id, st.id, start, end)
    return w


def _crew_for(w: World, st: Step) -> str:
    if st.trade == "mep":
        if st.code != "K5" and st.site_id in SPARKS_CREW_BY_SITE:
            return SPARKS_CREW_BY_SITE[st.site_id]
        cid = f"VOLT-{st.site_id}"
        w.crews.setdefault(cid, Crew(cid, "VOLT", "mep", 6, f"Voltline crew {st.site_id}"))
        return cid
    gc = w.sites[st.site_id].org_id
    cid = f"{gc}-{st.trade}-{st.site_id}"  # one direct crew per trade per site
    w.crews.setdefault(cid, Crew(cid, gc, st.trade, st.headcount, f"{w.orgs[gc].name} {st.trade} ({st.site_id})"))
    return cid
```

(`seed.py` imports `forward_pass`, so implement Task 2's `app/schedule.py` before running this test; run Step 4 after Task 2 Step 3 if executing strictly in order, or implement both files now.)

- [ ] **Step 4: Run test to verify it passes** (after `app/schedule.py` exists)

Run: `uv run pytest tests/test_seed.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/config.py app/domain.py seed/ tests/test_seed.py
git commit -m "feat: programme loader and world seed"
```

---

### Task 2: Schedule propagation and critical path

**Files:**
- Create: `app/schedule.py`
- Test: `tests/test_schedule.py`

**Interfaces:**
- Consumes: `World`, `Step` (Task 1).
- Produces: `forward_pass(world, site_id, mode="confirmed", min_start=None) -> dict[str, tuple[int, int]]` (modes: `baseline`, `confirmed`, `risk`); `site_finish(dates) -> int`; `critical_steps(world, site_id, dates) -> set[str]`; `all_dates(world, mode="confirmed") -> dict[str, dict[str, tuple[int,int]]]`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schedule.py
from app.schedule import all_dates, critical_steps, forward_pass, site_finish
from seed.seed import build_world

def test_baseline_stages_on_day_220():
    w = build_world()
    d = all_dates(w, "baseline")
    assert d["A"]["A-J1"] == (220, 230)
    assert d["B"]["B-G5"][0] == 220
    assert d["C"]["C-K3"] == (225, 245)
    assert d["D"]["D-F7"][0] == 220
    assert site_finish(d["A"]) == 397

def test_j1_plus_5_moves_18_steps_and_finish():
    w = build_world()
    before = forward_pass(w, "A", "confirmed")
    w.steps["A-J1"].delay_days = 5
    after = forward_pass(w, "A", "confirmed")
    moved = {k for k in before if after[k] != before[k] and k != "A-J1"}
    assert len(moved) == 18
    assert all(after[k][0] - before[k][0] == 5 for k in moved)
    assert site_finish(after) == 402
    assert after["A-K3"] == (235, 255)

def test_min_start_models_late_crew_return():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    late = forward_pass(w, "A", "confirmed", min_start={"A-K3": 238})
    assert site_finish(late) == 405

def test_risk_mode_adds_risk_days_only_in_risk_mode():
    w = build_world()
    w.steps["A-J1"].risk_days = 2
    assert site_finish(forward_pass(w, "A", "confirmed")) == 397
    assert forward_pass(w, "A", "risk")["A-J1"] == (220, 232)

def test_k3_is_critical_after_delay():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    d = forward_pass(w, "A", "confirmed")
    assert "A-K3" in critical_steps(w, "A", d)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_schedule.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.schedule'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/schedule.py
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
        if min_start and sid in min_start:
            start = max(start, min_start[sid])
        extra = 0
        if mode in ("confirmed", "risk"):
            extra += st.delay_days
        if mode == "risk":
            extra += st.risk_days
        out[sid] = (start, start + st.days + extra)
    return out


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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_schedule.py tests/test_seed.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add app/schedule.py tests/test_schedule.py
git commit -m "feat: forward pass (baseline/confirmed/risk) and critical path"
```

---

### Task 3: Labour balance

**Files:**
- Create: `app/labour.py`
- Test: `tests/test_labour.py`

**Interfaces:**
- Consumes: `World`, `all_dates` (Task 2).
- Produces: `Imbalance` (frozen dataclass: type, site_id, step_id, crew_id, trade, start, end, workers); `imbalances(world, dates_by_site, window=(TODAY, TODAY+LOOKAHEAD_DAYS)) -> list[Imbalance]`; `diff_imbalances(before, after) -> dict` with keys `created`, `resolved` (lists of Imbalance); `effective_booking_end(world, booking) -> int`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_labour.py
from app.labour import diff_imbalances, imbalances
from app.schedule import all_dates
from seed.seed import build_world

def test_no_imbalances_in_lookahead_at_seed():
    w = build_world()
    assert imbalances(w, all_dates(w)) == []

def test_roof_delay_creates_exactly_one_mep_surplus():
    w = build_world()
    before = imbalances(w, all_dates(w))
    w.steps["A-J1"].delay_days = 5
    after = imbalances(w, all_dates(w))
    assert len(after) == 1
    i = after[0]
    assert (i.type, i.site_id, i.step_id, i.crew_id, i.trade, i.start, i.end, i.workers) == \
        ("SURPLUS", "A", "A-K3", "SPARKS-S1", "mep", 230, 235, 6)
    d = diff_imbalances(before, after)
    assert d["created"] == after and d["resolved"] == []

def test_booking_elsewhere_makes_crew_days_productive():
    from app.domain import Booking
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    w.bookings["x"] = Booking("x", "SPARKS-S1", "C-K3", 230, 235, source="swap")
    assert imbalances(w, all_dates(w)) == []

def test_clash_when_same_crew_needed_twice():
    from app.domain import Booking
    w = build_world()
    w.bookings["y"] = Booking("y", "SPARKS-S1", "C-K3", 230, 235, source="test")
    types = {i.type for i in imbalances(w, all_dates(w))}
    assert "CLASH" in types
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_labour.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.labour'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/labour.py
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
            out += [Imbalance("SURPLUS", st.site_id, step_id, crew_id, crew.trade, s, e, crew.size) for s, e in _runs(days)]
        for step_id, days in clash.items():
            st = world.steps[step_id]
            out += [Imbalance("CLASH", st.site_id, step_id, crew_id, crew.trade, s, e, crew.size) for s, e in _runs(days)]
    for st in world.steps.values():
        if not (st.has_crew and st.headcount):
            continue
        s, e = dates_by_site[st.site_id][st.id]
        own = [b for b in world.bookings.values() if b.step_id == st.id]
        short = [d for d in range(max(s, lo), min(e, hi))
                 if not any(b.start <= d < effective_booking_end(world, b) for b in own)]
        out += [Imbalance("SHORTAGE", st.site_id, st.id, None, st.trade, a, z, st.headcount) for a, z in _runs(short)]
    return sorted(out, key=lambda i: (i.start, i.site_id, i.step_id, i.type))


def diff_imbalances(before: list[Imbalance], after: list[Imbalance]) -> dict:
    b, a = set(before), set(after)
    return {"created": [i for i in after if i not in b], "resolved": [i for i in before if i not in a]}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_labour.py -v`
Expected: PASS (4 tests). If `test_no_imbalances_in_lookahead_at_seed` fails, print the list, and fix the seed (never the test): the seed must have zero imbalances in the lookahead.

- [ ] **Step 5: Commit**

```bash
git add app/labour.py tests/test_labour.py
git commit -m "feat: labour balance (surplus, shortage, clash) and diff"
```

---

### Task 4: Sync engine: gaps and mechanisms (M1, M3, M8, M10)

**Files:**
- Create: `app/sync_engine.py`
- Test: `tests/test_sync_engine.py`

**Interfaces:**
- Consumes: `imbalances`, `all_dates`, `forward_pass`, `site_finish`, `critical_steps`.
- Produces: `Gap` and `Option` dataclasses; `open_gaps(world) -> list[Gap]`; `options_for(world, gap) -> list[Option]` (ranked); `link_active(world, org_a, org_b) -> bool`; `distance_km(site_a, site_b) -> float`; `approve_option(world, user, gap_id, mechanism) -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_sync_engine.py
from app.domain import Link
from app.sync_engine import open_gaps, options_for
from seed.seed import build_world

def _delayed():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    return w

def test_one_gap_with_warning_days():
    gaps = open_gaps(_delayed())
    assert len(gaps) == 1
    g = gaps[0]
    assert (g.type, g.step_id, g.start, g.end, g.warning_days) == ("SURPLUS", "A-K3", 230, 235, 10)

def test_options_before_link():
    w = _delayed()
    opts = {o.mechanism: o for o in options_for(w, open_gaps(w)[0])}
    assert not opts["M1"].feasible and "K5" in opts["M1"].reason
    assert opts["M3"].feasible and opts["M3"].days_protected == 3 and opts["M3"].start_by == 230
    m8 = opts["M8"]
    assert not m8.feasible and m8.needs_link_with == "RV"
    assert m8.target_step_id == "C-K3" and round(m8.distance_km, 1) == 1.7
    assert m8.days_protected == 3 and m8.idle_cost_avoided_gbp == 6000 and m8.start_by == 229

def test_m8_feasible_and_ranked_first_after_link():
    w = _delayed()
    w.links["L1"] = Link("L1", "NG", "RV", "priya", "pool M&E", status="ACTIVE")
    ranked = options_for(w, open_gaps(w)[0])
    assert ranked[0].mechanism == "M8" and ranked[0].feasible
    assert ranked[0].value_gbp == 3 * 8000 + 6000
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_sync_engine.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.sync_engine'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/sync_engine.py
import math
from dataclasses import asdict, dataclass, field

from app.config import CREW_DAY_GBP, MAX_SWAP_KM, RETURN_LAG_DAYS, TODAY
from app.domain import Booking, User, World
from app.labour import imbalances
from app.schedule import all_dates, critical_steps, forward_pass, site_finish

RELIABILITY = {"M1": 3, "M3": 3, "M8": 2, "M10": 2}


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


def open_gaps(world: World) -> list[Gap]:
    return [Gap(gap_id(i), i.type, i.site_id, i.step_id, i.crew_id, i.trade, i.start, i.end, i.workers,
                i.start - TODAY) for i in imbalances(world, all_dates(world))]


def _days_protected(world: World, gap: Gap) -> int:
    dates = forward_pass(world, gap.site_id, "confirmed")
    if gap.type != "SURPLUS" or gap.step_id not in critical_steps(world, gap.site_id, dates):
        return 0
    home_start = dates[gap.step_id][0]
    late = forward_pass(world, gap.site_id, "confirmed", min_start={gap.step_id: home_start + RETURN_LAG_DAYS})
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


def gap_days(gap: Gap) -> int:
    return gap.end - gap.start


def _m3(world, gap, dp) -> Option:
    return _base(world, gap, "M3", "Re-slot crew to new dates and notify downstream trades", True, None, 0, dp,
                 parties=[world.sites[gap.site_id].org_id])


def swap_candidates(world: World, gap: Gap) -> list[tuple]:
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
        s, e = dates[st.site_id][st.id]
        overlap = min(e, gap.end) - max(s, gap.start)
        target_gc = world.sites[st.site_id].org_id
        approved = any(a.sub_org_id == crew.org_id and a.gc_org_id == target_gc for a in world.approvals)
        km = distance_km(home, world.sites[st.site_id])
        if overlap >= min(3, gap_days(gap)) and approved and km <= MAX_SWAP_KM:
            out.append((st.id, b.crew_id, km))
    return sorted(out, key=lambda t: t[2])


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
    feasible = linked and returns_ok
    reason = None if feasible else ("Needs a link with a nearby project's company" if not linked
                                    else "Crew would not return in time")
    sub = world.orgs[world.crews[gap.crew_id].org_id].name
    return _base(world, gap, "M8",
                 f"Slot swap: {sub} crew works a nearby project days {gap.start}–{gap.end}, back on site day {home_start}",
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
    return _base(world, gap, "M10", f"Agency top-up via {world.orgs[a.sub_org_id].name}",
                 a.setup_days <= gap.warning_days, None if a.setup_days <= gap.warning_days else "Not enough warning",
                 a.setup_days, 0, parties=[gc, a.sub_org_id])


def options_for(world: World, gap: Gap) -> list[Option]:
    dp = _days_protected(world, gap)
    opts = [o for o in [_m1(world, gap, dp) if gap.type == "SURPLUS" else None, _m3(world, gap, dp),
                        _m8(world, gap, dp), _m10(world, gap)] if o]
    for o in opts:
        o.status = world.option_states.get(o.id, "PROPOSED")
        if o.status == "PROPOSED" and TODAY > o.start_by:
            o.status = "EXPIRED"
    return sorted(opts, key=lambda o: (not o.feasible, -o.value_gbp, -RELIABILITY.get(o.mechanism, 1), o.setup_days))


def approve_option(world: World, user: User, gap_id_: str, mechanism: str) -> dict:
    gap = next(g for g in open_gaps(world) if g.id == gap_id_)
    opt = next(o for o in options_for(world, gap) if o.mechanism == mechanism)
    if not opt.feasible:
        raise ValueError(opt.reason or "infeasible")
    world.option_states[opt.id] = "APPROVED"
    world.log("OptionApproved", user.id, gap.site_id, {"option_id": opt.id, "mechanism": mechanism})
    if mechanism == "M3":
        home_start, home_end = forward_pass(world, gap.site_id, "confirmed")[gap.step_id]
        for b in world.bookings.values():
            if b.step_id == gap.step_id and b.crew_id == gap.crew_id:
                b.start, b.end = home_start, home_end - world.steps[gap.step_id].delay_days
        world.option_states[opt.id] = "DONE"
        world.outcomes.append({"option_id": opt.id, "days_protected": opt.days_protected, "value_gbp": opt.value_gbp})
        world.log("BookingChanged", user.id, gap.site_id, {"crew_id": gap.crew_id, "step_id": gap.step_id})
        return {"status": "DONE", "option": opt.to_dict()}
    if mechanism == "M8":
        from app.network import send_cross_proposal
        cp = send_cross_proposal(world, user, gap, opt)
        world.option_states[opt.id] = "IN_PROGRESS"
        return {"status": "IN_PROGRESS", "cross_proposal_id": cp["id"], "option": opt.to_dict()}
    world.option_states[opt.id] = "APPROVED"
    return {"status": "APPROVED", "option": opt.to_dict()}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_sync_engine.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/sync_engine.py tests/test_sync_engine.py
git commit -m "feat: sync engine gaps and mechanisms M1/M3/M8/M10"
```

---

### Task 5: Network: links, pools, cross-company proposals

**Files:**
- Create: `app/network.py`
- Test: `tests/test_network.py`

**Interfaces:**
- Consumes: `World`, `Link`, `Booking`, `Gap`, `Option`, `open_gaps`.
- Produces: `anon_id(site_id) -> str`; `site_for_anon(world, anon) -> str`; `request_link(world, user, anon, purpose) -> Link`; `decide_link(world, user, link_id, accept, pool_terms=None) -> Link`; `send_cross_proposal(world, user, gap, opt) -> dict`; `decide_cross_proposal(world, user, cp_id, accept) -> dict`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_network.py
import pytest
from app.network import anon_id, decide_cross_proposal, decide_link, request_link
from app.sync_engine import approve_option, open_gaps
from seed.seed import build_world

def test_full_link_and_swap_flow():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    priya, marcus, sam = w.users["priya"], w.users["marcus"], w.users["sam"]
    link = request_link(w, priya, anon_id("C"), "pool M&E capacity")
    assert link.status == "REQUESTED" and link.org_b == "RV"
    with pytest.raises(PermissionError):
        decide_link(w, priya, link.id, True)
    decide_link(w, marcus, link.id, True, {"trades": ["mep"], "return_guarantee": True})
    assert w.links[link.id].status == "ACTIVE"
    gap = open_gaps(w)[0]
    res = approve_option(w, priya, gap.id, "M8")
    cp_id = res["cross_proposal_id"]
    decide_cross_proposal(w, marcus, cp_id, True)
    out = decide_cross_proposal(w, sam, cp_id, True)
    assert out["status"] == "AGREED"
    assert {p["org_id"] for p in out["proposals"]} == {"NG", "RV"}

def test_request_link_to_own_org_rejected():
    w = build_world()
    with pytest.raises(ValueError):
        request_link(w, w.users["priya"], anon_id("B"), "x")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_network.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.network'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/network.py
import hashlib

from app.domain import Link, User, World


def anon_id(site_id: str) -> str:
    return hashlib.sha1(f"sitesync:{site_id}".encode()).hexdigest()[:8]


def site_for_anon(world: World, anon: str) -> str:
    for sid in world.sites:
        if anon_id(sid) == anon:
            return sid
    raise KeyError(anon)


def request_link(world: World, user: User, anon: str, purpose: str) -> Link:
    target_org = world.sites[site_for_anon(world, anon)].org_id
    if target_org == user.org_id:
        raise ValueError("cannot link with your own company")
    link = Link(world.next_id("link"), user.org_id, target_org, user.id, purpose)
    world.links[link.id] = link
    world.log("LinkRequested", user.id, None, {"link_id": link.id, "to_org": target_org, "purpose": purpose})
    return link


def decide_link(world: World, user: User, link_id: str, accept: bool, pool_terms: dict | None = None) -> Link:
    link = world.links[link_id]
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
    cp = world.cross_proposals[cp_id]
    if user.org_id not in (cp["to_org"], cp["sub_org"]):
        raise PermissionError("not a party to this proposal")
    cp["accepted"][user.org_id] = accept
    world.log("ProposalAccepted" if accept else "ProposalDeclined", user.id, None, {"cross_proposal_id": cp_id})
    if not accept:
        cp["status"] = "DECLINED"
        return {"status": "DECLINED", "proposals": []}
    if all(cp["accepted"].get(o) for o in (cp["to_org"], cp["sub_org"])):
        cp["status"] = "AGREED"
        from app.proposals import booking_proposal
        p1 = booking_proposal(world, cp, org_id=cp["to_org"], kind="add_swap_booking")
        p2 = booking_proposal(world, cp, org_id=cp["from_org"], kind="confirm_return")
        return {"status": "AGREED", "proposals": [p1, p2]}
    return {"status": "PARTIAL", "proposals": []}
```

(`booking_proposal` is defined in Task 6; implement Task 6 before running Step 4.)

- [ ] **Step 4: Run tests to verify they pass** (after Task 6 Step 3)

Run: `uv run pytest tests/test_network.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/network.py tests/test_network.py
git commit -m "feat: links, pools and cross-company proposals"
```

---

### Task 6: Proposed changes, knock-on preview, confirmation rules

**Files:**
- Create: `app/proposals.py`
- Test: `tests/test_proposals.py`

**Interfaces:**
- Consumes: `World`, `forward_pass`, `site_finish`, `critical_steps`, `imbalances`, `diff_imbalances`, `all_dates`.
- Produces: `build_proposal(world, user, site_id, changes, source) -> dict` where `changes = [{"step_id", "field": "delay_days", "to": int}]`; returned dict keys: `id, site_id, org_id, created_by, based_on_version, changes, source, status, needs_pm, knock_on`; `knock_on = {"moved": [{"step_id","code","from","to"}], "finish_from", "finish_to", "labour": {"created": [...], "resolved": [...]}}`; `decide_proposal(world, user, pid, accept) -> dict`; `booking_proposal(world, cp, org_id, kind) -> dict`; `StaleProposal` exception.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_proposals.py
import pytest
from app.proposals import StaleProposal, build_proposal, decide_proposal
from seed.seed import build_world

SRC = {"kind": "voice", "excerpt": "roofing delayed, heavy rain, about five days"}

def _prop(w):
    return build_proposal(w, w.users["dan"], "A", [{"step_id": "A-J1", "field": "delay_days", "to": 5}], SRC)

def test_knock_on_preview_has_dates_and_labour():
    w = build_world()
    p = _prop(w)
    k = p["knock_on"]
    assert len([m for m in k["moved"] if m["step_id"] != "A-J1"]) == 18
    assert (k["finish_from"], k["finish_to"]) == (397, 402)
    assert [(i["type"], i["step_id"], i["start"], i["end"]) for i in k["labour"]["created"]] == [("SURPLUS", "A-K3", 230, 235)]
    assert p["needs_pm"] is True
    assert w.steps["A-J1"].delay_days == 0  # preview only

def test_site_manager_then_pm_confirm():
    w = build_world()
    p = _prop(w)
    r1 = decide_proposal(w, w.users["dan"], p["id"], True)
    assert r1["status"] == "SITE_CONFIRMED" and w.steps["A-J1"].delay_days == 0
    r2 = decide_proposal(w, w.users["priya"], p["id"], True)
    assert r2["status"] == "APPLIED" and w.steps["A-J1"].delay_days == 5
    assert w.versions["A"] == 1 and w.snapshots[-1]["site_id"] == "A"

def test_stale_or_repeated_decision_rejected():
    w = build_world()
    p = _prop(w)
    decide_proposal(w, w.users["priya"], p["id"], True)
    with pytest.raises(StaleProposal):
        decide_proposal(w, w.users["priya"], p["id"], True)

def test_other_org_cannot_decide():
    w = build_world()
    p = _prop(w)
    with pytest.raises(PermissionError):
        decide_proposal(w, w.users["marcus"], p["id"], True)

def test_invalid_delay_blocked():
    w = build_world()
    with pytest.raises(ValueError):
        build_proposal(w, w.users["dan"], "A", [{"step_id": "A-J1", "field": "delay_days", "to": 90}], SRC)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_proposals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.proposals'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/proposals.py
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
    slip_on_critical = any(m["step_id"] in crit and m["to"][1] - m["from"][1] >= PM_CRITICAL_SLIP_DAYS for m in moved)
    diff = diff_imbalances(before_imb, after_imb)
    for c in changes:
        c["from"] = world.steps[c["step_id"]].delay_days
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
         "needs_pm": True, "knock_on": {"moved": [], "finish_from": None, "finish_to": None,
                                          "labour": {"created": [], "resolved": []}}, "kind": kind}
    world.proposals[p["id"]] = p
    return p
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_proposals.py tests/test_network.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Commit**

```bash
git add app/proposals.py tests/test_proposals.py
git commit -m "feat: proposed changes with knock-on preview and confirmation rules"
```

---

### Task 7: Ingestion: deterministic extractor, LLM chain, Plaud

**Files:**
- Create: `app/vocab.py`, `app/llm.py`, `app/ingest.py`, `app/plaud.py`
- Test: `tests/test_ingest.py`, `tests/test_plaud.py`

**Interfaces:**
- Consumes: `World`.
- Produces: `words_to_days(text) -> int | None`; `match_steps(world, site_id, text) -> list[str]` (step codes); `ExtractedUpdate` pydantic model (fields: `step_code: str | None`, `candidates: list[str]`, `delay_days: int | None`, `reason: str`, `excerpt: str`, `confidence: float`); `extract_updates(world, site_id, text) -> list[ExtractedUpdate]`; `llm.CALL_LOG: list[dict]`; `llm.extract_json(system, user, model_cls) -> BaseModel` raising `LLMUnavailable`; `plaud.parse_transcript(raw) -> str`; `plaud.parse_ids(raw) -> list[str]`; `plaud.recent_ids() -> list[str]`; `plaud.transcript(file_id) -> str`; `PlaudError`.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_ingest.py
from app import ingest
from app.vocab import match_steps, words_to_days
from seed.seed import build_world

def test_words_to_days():
    assert words_to_days("about five days") == 5
    assert words_to_days("a week") == 5
    assert words_to_days("couple of days") == 2
    assert words_to_days("3 days") == 3
    assert words_to_days("all good") is None

def test_match_roof():
    w = build_world()
    assert match_steps(w, "A", "roofing delayed, heavy rain")[0] == "J1"

def test_extract_demo_transcript_offline(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    w = build_world()
    ups = ingest.extract_updates(w, "A", "Roofing delayed, heavy rain, about five days.")
    assert len(ups) == 1 and ups[0].step_code == "J1" and ups[0].delay_days == 5

def test_no_update_for_chatter(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    w = build_world()
    assert ingest.extract_updates(w, "A", "All good today, deliveries arrived.") == []
```

```python
# tests/test_plaud.py
from app.plaud import parse_ids, parse_transcript

def test_parse_transcript_strips_timestamps_and_speakers():
    raw = "[00:00 - 00:04] Speaker 1: Roofing delayed,\n[00:04 - 00:09] Speaker 1: heavy rain, about five days."
    assert parse_transcript(raw) == "Roofing delayed, heavy rain, about five days."

def test_parse_ids_finds_hex_ids():
    raw = "ID                                Name\n0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b  Site A 07:42\n"
    assert parse_ids(raw) == ["0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_ingest.py tests/test_plaud.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# app/vocab.py
import re

from app.domain import World

SYNONYMS = {
    "J1": ["roof", "roofing", "membrane", "waterproofing"],
    "J2": ["windows lower", "glazing lower"], "J3": ["windows upper", "glazing upper"],
    "J4": ["cladding lower", "brick slip"], "J5": ["cladding upper"],
    "K1": ["blockwork lower", "party walls"], "K3": ["first fix", "m&e first fix", "electrics first fix"],
    "K5": ["risers", "plant room"], "K6": ["first fix inspection", "inspection"],
    "K8": ["drylining lower", "plastering", "screed"], "H7": ["props", "back-propping"],
}
NUMBERS = {"one": 1, "a": 1, "two": 2, "couple": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def words_to_days(text: str) -> int | None:
    t = text.lower()
    m = re.search(r"(\d+)\s*(working\s+)?days?", t)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(a|one|two|couple)\s+(of\s+)?weeks?\b", t)
    if m:
        return 5 * NUMBERS[m.group(1)]
    m = re.search(r"\b(" + "|".join(NUMBERS) + r")\s+(of\s+)?days?\b", t)
    if m:
        return NUMBERS[m.group(1)]
    return None


def match_steps(world: World, site_id: str, text: str) -> list[str]:
    t = text.lower()
    hits = []
    for code, words in SYNONYMS.items():
        if any(w in t for w in words):
            hits.append((max(len(w) for w in words if w in t), code))
    for st in world.steps.values():
        if st.site_id == site_id and st.name.lower() in t:
            hits.append((len(st.name), st.code))
    return [c for _, c in sorted(hits, reverse=True)]
```

```python
# app/llm.py
import json
import os
import time

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from app.config import LLM_PROVIDERS

PROVIDERS = {
    "crusoe": {"base_url": os.getenv("CRUSOE_BASE_URL", "https://api.inference.crusoecloud.com/v1"),
               "key_env": "CRUSOE_API_KEY", "model": os.getenv("CRUSOE_MODEL_EXTRACT", "openai/gpt-oss-120b")},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_env": "OPENROUTER_API_KEY",
                   "model": "openai/gpt-oss-120b"},
}
CALL_LOG: list[dict] = []


class LLMUnavailable(Exception):
    pass


def _formats(model_cls: type[BaseModel]):
    schema = model_cls.model_json_schema()
    yield {"type": "json_schema", "json_schema": {"name": model_cls.__name__, "schema": schema}}
    yield {"type": "json_object"}
    yield None


def extract_json(system: str, user: str, model_cls: type[BaseModel]) -> BaseModel:
    for name in LLM_PROVIDERS:
        cfg = PROVIDERS.get(name)
        key = os.getenv(cfg["key_env"]) if cfg else None
        if not key:
            continue
        client = OpenAI(api_key=key, base_url=cfg["base_url"], timeout=20)
        for fmt in _formats(model_cls):
            t0 = time.time()
            try:
                kw = {"response_format": fmt} if fmt else {}
                r = client.chat.completions.create(model=cfg["model"], temperature=0, messages=[
                    {"role": "system", "content": system + " Reply with JSON only."},
                    {"role": "user", "content": user}], **kw)
                text = r.choices[0].message.content or ""
                text = text[text.find("{"): text.rfind("}") + 1]
                out = model_cls.model_validate(json.loads(text))
                CALL_LOG.append({"provider": name, "model": cfg["model"], "ok": True,
                                 "latency_ms": int((time.time() - t0) * 1000),
                                 "prompt_tokens": getattr(r.usage, "prompt_tokens", None),
                                 "completion_tokens": getattr(r.usage, "completion_tokens", None)})
                return out
            except (ValidationError, ValueError, json.JSONDecodeError, Exception) as e:  # noqa: BLE001
                CALL_LOG.append({"provider": name, "model": cfg["model"], "ok": False, "error": str(e)[:200],
                                 "latency_ms": int((time.time() - t0) * 1000)})
    raise LLMUnavailable("no provider succeeded")
```

```python
# app/ingest.py
from pydantic import BaseModel

from app import llm
from app.domain import World
from app.vocab import match_steps, words_to_days


class ExtractedUpdate(BaseModel):
    step_code: str | None
    candidates: list[str] = []
    delay_days: int | None
    reason: str
    excerpt: str
    confidence: float


class ExtractedList(BaseModel):
    updates: list[ExtractedUpdate]


REASONS = ["rain", "weather", "wind", "delivery", "material", "inspection", "labour", "access", "design"]


def _catalogue(world: World, site_id: str) -> str:
    return "\n".join(f"{s.code}: {s.name} ({s.trade})" for s in world.steps.values() if s.site_id == site_id)


def _llm_extract(world: World, site_id: str, text: str) -> list[ExtractedUpdate] | None:
    system = ("You turn construction site voice notes into schedule delay updates. Choose step_code ONLY from the "
              "catalogue. If unsure, set step_code null and list candidates. If the note reports no delay, "
              "return an empty list. delay_days is working days (a week = 5).")
    user = f"Catalogue:\n{_catalogue(world, site_id)}\n\nVoice note:\n{text}\n\nReturn {{\"updates\": [...]}}"
    try:
        return llm.extract_json(system, user, ExtractedList).updates
    except llm.LLMUnavailable:
        return None


def _deterministic(world: World, site_id: str, text: str) -> list[ExtractedUpdate]:
    days = words_to_days(text)
    steps = match_steps(world, site_id, text)
    if days is None or not steps or "delay" not in text.lower() and "late" not in text.lower():
        return []
    reason = next((r for r in REASONS if r in text.lower()), "unspecified")
    return [ExtractedUpdate(step_code=steps[0], candidates=steps[1:3], delay_days=days, reason=reason,
                            excerpt=text.strip(), confidence=0.6)]


def extract_updates(world: World, site_id: str, text: str) -> list[ExtractedUpdate]:
    codes = {s.code for s in world.steps.values() if s.site_id == site_id}
    got = _llm_extract(world, site_id, text)
    if got is not None:
        return [u for u in got if u.delay_days and (u.step_code in codes or u.candidates)]
    return _deterministic(world, site_id, text)
```

```python
# app/plaud.py
import re
import subprocess


class PlaudError(Exception):
    pass


def parse_transcript(raw: str) -> str:
    parts = []
    for line in raw.splitlines():
        line = re.sub(r"^\s*\[\d{1,2}:\d{2}(:\d{2})?\s*-\s*\d{1,2}:\d{2}(:\d{2})?\]\s*", "", line)
        line = re.sub(r"^[^:]{1,30}:\s+", "", line)
        if line.strip():
            parts.append(line.strip())
    return " ".join(parts)


def parse_ids(raw: str) -> list[str]:
    return re.findall(r"\b[0-9a-f]{24,40}\b", raw)


def _run(args: list[str]) -> str:
    try:
        r = subprocess.run(["plaud", *args], capture_output=True, text=True, timeout=30)
    except FileNotFoundError as e:
        raise PlaudError("plaud CLI not installed") from e
    if r.returncode == 2:
        raise PlaudError("Plaud login expired: run `plaud login`")
    if r.returncode != 0:
        raise PlaudError(r.stderr.strip() or f"plaud exited {r.returncode}")
    return r.stdout


def recent_ids() -> list[str]:
    return parse_ids(_run(["recent", "--days", "1"]))


def transcript(file_id: str) -> str:
    try:
        return parse_transcript(_run(["transcript", file_id, "--polished"]))
    except PlaudError:
        return parse_transcript(_run(["transcript", file_id]))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_ingest.py tests/test_plaud.py -v`
Expected: PASS (6 tests). Then once `plaud login` is done, run `plaud recent --days 1` by hand and confirm `parse_ids` finds the id format; adjust the regex in `parse_ids` if the real ids differ, and add that real line as a test case.

- [ ] **Step 5: Commit**

```bash
git add app/vocab.py app/llm.py app/ingest.py app/plaud.py tests/test_ingest.py tests/test_plaud.py
git commit -m "feat: ingestion with LLM chain, deterministic fallback, Plaud CLI wrapper"
```

---

### Task 8: Signals (risk flags, Open-Meteo)

**Files:**
- Create: `app/signals.py`
- Test: `tests/test_signals.py`

**Interfaces:**
- Consumes: `World`, `forward_pass`, `site_finish`.
- Produces: `raise_risk(world, site_id, step_code, days, kind, detail) -> dict` (returns `{question, risk_finish, confirmed_finish}`); `clear_risk(world, site_id, step_code)`; `wet_days(daily_precip_mm, threshold=2.0) -> list[int]`; `refresh_weather(world) -> list[dict]` (network; not unit-tested).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_signals.py
from app.schedule import forward_pass, site_finish
from app.signals import clear_risk, raise_risk, wet_days
from seed.seed import build_world

def test_risk_moves_risk_forecast_not_confirmed():
    w = build_world()
    r = raise_risk(w, "A", "J1", 2, "weather", "Rain Thu–Fri")
    assert r["risk_finish"] == 399 and r["confirmed_finish"] == 397
    assert "J1" in r["question"]
    assert site_finish(forward_pass(w, "A", "confirmed")) == 397
    clear_risk(w, "A", "J1")
    assert site_finish(forward_pass(w, "A", "risk")) == 397

def test_wet_days():
    assert wet_days([0.0, 5.1, 3.0, 0.4]) == [1, 2]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_signals.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.signals'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/signals.py
import httpx

from app.config import TODAY
from app.domain import World
from app.schedule import forward_pass, site_finish


def raise_risk(world: World, site_id: str, step_code: str, days: int, kind: str, detail: str) -> dict:
    st = world.steps[f"{site_id}-{step_code}"]
    st.risk_days = days
    world.log("RiskFlagRaised", None, site_id, {"step_id": st.id, "days": days, "kind": kind, "detail": detail},
              {"kind": "signal", "excerpt": detail})
    return {"question": f"{detail}: {st.code} {st.name} at risk of +{days} days. Confirm impact?",
            "risk_finish": site_finish(forward_pass(world, site_id, "risk")),
            "confirmed_finish": site_finish(forward_pass(world, site_id, "confirmed"))}


def clear_risk(world: World, site_id: str, step_code: str) -> None:
    st = world.steps[f"{site_id}-{step_code}"]
    st.risk_days = 0
    world.log("RiskFlagCleared", None, site_id, {"step_id": st.id})


def wet_days(daily_precip_mm: list[float], threshold: float = 2.0) -> list[int]:
    return [i for i, mm in enumerate(daily_precip_mm) if mm is not None and mm >= threshold]


def refresh_weather(world: World) -> list[dict]:
    flags = []
    for site in world.sites.values():
        r = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": site.lat, "longitude": site.lon, "daily": "precipitation_sum", "forecast_days": 7})
        r.raise_for_status()
        wet = wet_days(r.json()["daily"]["precipitation_sum"])
        dates = forward_pass(world, site.id, "confirmed")
        for st in world.steps.values():
            if st.site_id != site.id or not st.weather_sensitive:
                continue
            s, e = dates[st.id]
            hit = [d for d in wet if s <= TODAY + d < e]
            if hit:
                flags.append({"site_id": site.id, "step": st.code,
                              **raise_risk(world, site.id, st.code, len(hit), "weather", f"Rain forecast on {len(hit)} day(s)")})
    return flags
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_signals.py -v`
Expected: PASS (2 tests)

- [ ] **Step 5: Commit**

```bash
git add app/signals.py tests/test_signals.py
git commit -m "feat: risk signals and Open-Meteo weather refresh"
```

---

### Task 9: Views: scopes and anonymisation

**Files:**
- Create: `app/views.py`
- Test: `tests/test_views.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `sites_view(world, user)`, `timeline_view(world, user, site_id)`, `labour_view(world, user, site_id)`, `sync_board_view(world, user)`, `city_view(world, user)`, `links_view(world, user)`, `cross_proposals_view(world, user)`, `proposals_view(world, user, site_id)`; all return JSON-able dicts/lists; raise `PermissionError` on out-of-scope site.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_views.py
import json
from app.views import city_view, sites_view, sync_board_view, timeline_view
from seed.seed import build_world

FORBIDDEN_FOR_NG = ["Bow Wharf", "Canning Town", "\"C-", "\"D-", "Marcus", "Riverside"]

def _delayed():
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    return w

def test_priya_sees_only_own_sites_and_no_leaks():
    w = _delayed()
    p = w.users["priya"]
    blob = json.dumps([sites_view(w, p), sync_board_view(w, p), city_view(w, p), timeline_view(w, p, "A")])
    assert {s["id"] for s in sites_view(w, p)} == {"A", "B"}
    for f in FORBIDDEN_FOR_NG:
        assert f not in blob, f

def test_dan_cannot_open_site_b():
    import pytest
    w = build_world()
    with pytest.raises(PermissionError):
        timeline_view(w, w.users["dan"], "B")

def test_city_view_is_anonymised():
    w = build_world()
    cv = city_view(w, w.users["priya"])
    assert len(cv) == 2
    assert all(set(p) == {"anon_id", "area", "distance_band", "phase", "windows"} for p in cv)

def test_sync_board_shows_gap_and_needs_link():
    w = _delayed()
    board = sync_board_view(w, w.users["priya"])
    g = board["gaps"][0]
    assert g["step_code"] == "K3" and g["warning_days"] == 10
    m8 = next(o for o in g["options"] if o["mechanism"] == "M8")
    assert m8["needs_link"] is True and "target_anon_id" in m8
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_views.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.views'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/views.py
from collections import defaultdict
from dataclasses import asdict

from app.config import CREW_DAY_GBP, LOOKAHEAD_DAYS, TODAY
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


def _check(world, user, site_id):
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
    _check(world, user, site_id)
    b, c, r = (forward_pass(world, site_id, m) for m in ("baseline", "confirmed", "risk"))
    crit = critical_steps(world, site_id, c)
    steps = []
    for st in sorted((s for s in world.steps.values() if s.site_id == site_id), key=lambda s: b[s.id][0]):
        crews = [world.crews[bk.crew_id].name for bk in world.bookings.values() if bk.step_id == st.id]
        steps.append({"id": st.id, "code": st.code, "name": st.name, "trade": st.trade, "kind": st.kind,
                      "weather_sensitive": st.weather_sensitive, "risk_note": st.risk_note,
                      "base": list(b[st.id]), "confirmed": list(c[st.id]), "risk": list(r[st.id]),
                      "critical": st.id in crit, "risk_flag": st.risk_days > 0, "crews": crews})
    return {"site_id": site_id, "today": TODAY, "steps": steps}


def labour_view(world: World, user: User, site_id: str) -> dict:
    _check(world, user, site_id)
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
    d["needs_link"] = o.needs_link_with is not None
    return d


def sync_board_view(world: World, user: User) -> dict:
    sites = set(visible_sites(world, user))
    gaps = []
    for g in open_gaps(world):
        if g.site_id not in sites:
            continue
        st = world.steps[g.step_id]
        gaps.append({"id": g.id, "type": g.type, "site_id": g.site_id, "step_code": st.code, "step_name": st.name,
                     "trade": g.trade, "crew": world.crews[g.crew_id].name if g.crew_id else None,
                     "start": g.start, "end": g.end, "workers": g.workers, "warning_days": g.warning_days,
                     "idle_cost_gbp": (g.end - g.start) * CREW_DAY_GBP if g.type == "SURPLUS" else 0,
                     "options": [_option_view(world, user, o) for o in options_for(world, g)]})
    outcomes = [o for o in world.outcomes if o.get("org_id", user.org_id) == user.org_id]
    return {"gaps": sorted(gaps, key=lambda g: g["start"]), "outcomes": outcomes,
            "days_protected": sum(o["days_protected"] for o in outcomes)}


def _nearest_km(world, user, site) -> float:
    own = [world.sites[s] for s in visible_sites(world, user)] or list(world.sites.values())
    return min(distance_km(o, site) for o in own)


def city_view(world: World, user: User) -> list[dict]:
    dates = all_dates(world)
    out = []
    for sid, site in world.sites.items():
        if site.org_id == user.org_id or not site.publish or site.confidential:
            continue
        active = [s for s in world.steps.values() if s.site_id == sid
                  and dates[sid][s.id][0] <= TODAY < dates[sid][s.id][1] and s.days]
        phase = active[0].phase if active else "Not started"
        windows: dict[str, set[int]] = defaultdict(set)
        for s in world.steps.values():
            if s.site_id == sid and s.headcount:
                a, e = dates[sid][s.id]
                for d in range(max(a, TODAY), min(e, TODAY + 6 * 5)):
                    windows[s.trade].add(d // 5)
        wl = [{"trade": t, "kind": "need", "week_from": min(w), "week_to": max(w)} for t, w in windows.items()]
        for i in imbalances(world, dates):
            if i.site_id == sid and i.type == "SURPLUS":
                wl.append({"trade": i.trade, "kind": "surplus", "week_from": i.start // 5, "week_to": (i.end - 1) // 5})
        km = _nearest_km(world, user, site)
        out.append({"anon_id": anon_id(sid), "area": site.area, "distance_band": f"~{round(km)} km",
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
        out.append({"id": cp["id"], "status": cp["status"], "start": cp["start"], "end": cp["end"],
                    "trade": world.crews[cp["crew_id"]].trade,
                    "your_decision": cp["accepted"].get(user.org_id),
                    "from": world.orgs[cp["from_org"]].name,
                    "target_site": world.sites[world.steps[cp["target_step_id"]].site_id].name
                    if agreed or user.org_id in (cp["to_org"], cp["sub_org"]) else "a nearby project",
                    "crew": world.crews[cp["crew_id"]].name if user.org_id != cp["to_org"] or agreed else "a vetted M&E crew"})
    return out


def proposals_view(world: World, user: User, site_id: str) -> list[dict]:
    _check(world, user, site_id)
    return [p for p in world.proposals.values() if p["site_id"] == site_id and p["status"] in ("PENDING", "SITE_CONFIRMED")]
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_views.py -v`
Expected: PASS (4 tests)

- [ ] **Step 5: Commit**

```bash
git add app/views.py tests/test_views.py
git commit -m "feat: role-scoped views and anonymised city view"
```

---

### Task 10: FastAPI routes

**Files:**
- Create: `app/main.py`, `scripts/dump_fixtures.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: all modules.
- Produces: HTTP API per spec §8 (MVP subset below); `app.main.app`; module-level `STATE = {"world": World}`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
from fastapi.testclient import TestClient
from app import ingest
from app.main import app

c = TestClient(app)
H = lambda u: {"X-User-Id": u}

def setup_function():
    c.post("/api/demo/reset", headers=H("priya"))

def test_unknown_user_401():
    assert c.get("/api/sites").status_code == 401
    assert c.get("/api/sites", headers=H("nobody")).json()["error"] == "unknown_user"

def test_demo_story_end_to_end(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    p = c.post("/api/ingest/text", headers=H("dan"), json={"site_id": "A",
               "text": "Roofing delayed, heavy rain, about five days."}).json()
    pid = p["proposals"][0]["id"]
    assert c.post(f"/api/proposals/{pid}/decide", headers=H("dan"), json={"accept": True}).json()["status"] == "SITE_CONFIRMED"
    assert c.post(f"/api/proposals/{pid}/decide", headers=H("priya"), json={"accept": True}).json()["status"] == "APPLIED"
    assert c.post(f"/api/proposals/{pid}/decide", headers=H("priya"), json={"accept": True}).status_code == 409
    board = c.get("/api/sync-board", headers=H("priya")).json()
    gap = board["gaps"][0]
    anon = next(o for o in gap["options"] if o["mechanism"] == "M8")["target_anon_id"]
    link = c.post("/api/links", headers=H("priya"), json={"anon_id": anon, "purpose": "pool M&E"}).json()
    c.post(f"/api/links/{link['id']}/decide", headers=H("marcus"), json={"accept": True, "pool_terms": {"trades": ["mep"]}})
    r = c.post("/api/options/approve", headers=H("priya"), json={"gap_id": gap["id"], "mechanism": "M8"}).json()
    cp = r["cross_proposal_id"]
    c.post(f"/api/cross-proposals/{cp}/decide", headers=H("marcus"), json={"accept": True})
    c.post(f"/api/cross-proposals/{cp}/decide", headers=H("sam"), json={"accept": True})
    for user, site in (("marcus", "C"), ("priya", "A")):
        for prop in c.get(f"/api/proposals?site_id={site}", headers=H(user)).json():
            c.post(f"/api/proposals/{prop['id']}/decide", headers=H(user), json={"accept": True})
    assert c.get("/api/sync-board", headers=H("priya")).json()["gaps"] == []

def test_reset_clears_everything():
    c.post("/api/links", headers=H("priya"), json={"anon_id": c.get("/api/city", headers=H("priya")).json()[0]["anon_id"], "purpose": "x"})
    c.post("/api/demo/reset", headers=H("priya"))
    assert c.get("/api/links", headers=H("priya")).json() == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.main'`

- [ ] **Step 3: Write minimal implementation**

```python
# app/main.py
from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app import ingest, llm, plaud, signals, views
from app.network import decide_cross_proposal, decide_link, request_link
from app.proposals import StaleProposal, build_proposal, decide_proposal
from app.sync_engine import approve_option
from seed.seed import build_world

app = FastAPI(title="SiteSync")
STATE = {"world": build_world()}
STATIC = Path(__file__).parent.parent / "static"


class ApiError(Exception):
    def __init__(self, status: int, error: str, detail: str = ""):
        self.status, self.error, self.detail = status, error, detail


@app.exception_handler(ApiError)
async def api_error(_: Request, e: ApiError):
    return JSONResponse({"error": e.error, "detail": e.detail}, status_code=e.status)


@app.exception_handler(PermissionError)
async def forbidden(_: Request, e: PermissionError):
    return JSONResponse({"error": "forbidden", "detail": str(e)}, status_code=403)


@app.exception_handler(StaleProposal)
async def stale(_: Request, e: StaleProposal):
    return JSONResponse({"error": "stale", "detail": "already decided or the site changed since"}, status_code=409)


@app.exception_handler(ValueError)
async def bad(_: Request, e: ValueError):
    return JSONResponse({"error": "invalid", "detail": str(e)}, status_code=400)


def W():
    return STATE["world"]


def user_of(x_user_id: str | None):
    if not x_user_id or x_user_id not in W().users:
        raise ApiError(401, "unknown_user", "send X-User-Id")
    return W().users[x_user_id]


class TextIn(BaseModel):
    site_id: str
    text: str


class PlaudIn(BaseModel):
    site_id: str
    file_id: str | None = None


class DecideIn(BaseModel):
    accept: bool
    pool_terms: dict | None = None


class LinkIn(BaseModel):
    anon_id: str
    purpose: str


class ApproveIn(BaseModel):
    gap_id: str
    mechanism: str


class SignalIn(BaseModel):
    site_id: str
    step_code: str
    days: int
    kind: str = "weather"
    detail: str = "Rain forecast"


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/me")
def me(x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    return {"id": u.id, "name": u.name, "role": u.role, "org": W().orgs.get(u.org_id).name if u.org_id in W().orgs else "SiteSync",
            "sites": views.visible_sites(W(), u)}


@app.get("/api/users")
def users():
    return [{"id": u.id, "name": u.name, "role": u.role} for u in W().users.values()]


@app.get("/api/sites")
def sites(x_user_id: str | None = Header(None)):
    return views.sites_view(W(), user_of(x_user_id))


@app.get("/api/sites/{site_id}/timeline")
def timeline(site_id: str, x_user_id: str | None = Header(None)):
    return views.timeline_view(W(), user_of(x_user_id), site_id)


@app.get("/api/sites/{site_id}/labour")
def labour(site_id: str, x_user_id: str | None = Header(None)):
    return views.labour_view(W(), user_of(x_user_id), site_id)


def _propose_from_text(u, site_id: str, text: str, source_kind: str, extra: dict | None = None) -> dict:
    views._check(W(), u, site_id)
    ups = ingest.extract_updates(W(), site_id, text)
    if not ups:
        return {"proposals": [], "message": "No schedule change found in this note.", "text": text}
    props, candidates = [], []
    for up in ups:
        if not up.step_code:
            candidates.append(up.model_dump())
            continue
        step_id = f"{site_id}-{up.step_code}"
        cur = W().steps[step_id].delay_days
        props.append(build_proposal(W(), u, site_id, [{"step_id": step_id, "field": "delay_days",
                                                       "to": cur + up.delay_days}],
                                    {"kind": source_kind, "excerpt": up.excerpt, "reason": up.reason,
                                     "confidence": up.confidence, **(extra or {})}))
    return {"proposals": props, "candidates": candidates, "text": text}


@app.post("/api/ingest/text")
def ingest_text(body: TextIn, x_user_id: str | None = Header(None)):
    return _propose_from_text(user_of(x_user_id), body.site_id, body.text, "typed")


@app.get("/api/plaud/recordings")
def plaud_recordings(x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    try:
        return {"ids": plaud.recent_ids()}
    except plaud.PlaudError as e:
        raise ApiError(502, "plaud", str(e))


@app.post("/api/ingest/plaud")
def ingest_plaud(body: PlaudIn, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    try:
        fid = body.file_id or (plaud.recent_ids() or [None])[0]
        if not fid:
            raise ApiError(404, "no_recording", "No Plaud recording today (did you tap Generate?)")
        text = plaud.transcript(fid)
    except plaud.PlaudError as e:
        raise ApiError(502, "plaud", str(e))
    return _propose_from_text(u, body.site_id, text, "voice", {"plaud_file_id": fid})


@app.get("/api/proposals")
def proposals(site_id: str, x_user_id: str | None = Header(None)):
    return views.proposals_view(W(), user_of(x_user_id), site_id)


@app.post("/api/proposals/{pid}/decide")
def decide(pid: str, body: DecideIn, x_user_id: str | None = Header(None)):
    if pid not in W().proposals:
        raise ApiError(404, "not_found", pid)
    return decide_proposal(W(), user_of(x_user_id), pid, body.accept)


@app.post("/api/signals")
def signal(body: SignalIn, x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    return signals.raise_risk(W(), body.site_id, body.step_code, body.days, body.kind, body.detail)


@app.post("/api/signals/weather/refresh")
def weather(x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    return signals.refresh_weather(W())


@app.get("/api/sync-board")
def sync_board(x_user_id: str | None = Header(None)):
    return views.sync_board_view(W(), user_of(x_user_id))


@app.post("/api/options/approve")
def approve(body: ApproveIn, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    if u.role != "PM":
        raise PermissionError("only a PM can approve options")
    return approve_option(W(), u, body.gap_id, body.mechanism)


@app.get("/api/city")
def city(x_user_id: str | None = Header(None)):
    return views.city_view(W(), user_of(x_user_id))


@app.post("/api/links")
def link_request(body: LinkIn, x_user_id: str | None = Header(None)):
    l = request_link(W(), user_of(x_user_id), body.anon_id, body.purpose)
    return {"id": l.id, "status": l.status}


@app.post("/api/links/{link_id}/decide")
def link_decide(link_id: str, body: DecideIn, x_user_id: str | None = Header(None)):
    l = decide_link(W(), user_of(x_user_id), link_id, body.accept, body.pool_terms)
    return {"id": l.id, "status": l.status, "pool": l.pool}


@app.get("/api/links")
def links(x_user_id: str | None = Header(None)):
    return views.links_view(W(), user_of(x_user_id))


@app.get("/api/cross-proposals")
def cross(x_user_id: str | None = Header(None)):
    return views.cross_proposals_view(W(), user_of(x_user_id))


@app.post("/api/cross-proposals/{cp_id}/decide")
def cross_decide(cp_id: str, body: DecideIn, x_user_id: str | None = Header(None)):
    return decide_cross_proposal(W(), user_of(x_user_id), cp_id, body.accept)


@app.get("/api/events")
def events(site_id: str | None = None, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    mine = set(views.visible_sites(W(), u))
    return [e for e in W().events if e["site_id"] in mine or (e["site_id"] is None and e["user_id"] == u.id)]


@app.get("/api/llm/log")
def llm_log():
    return {"calls": llm.CALL_LOG[-50:]}


@app.post("/api/demo/reset")
def reset():
    STATE["world"] = build_world()
    llm.CALL_LOG.clear()
    return {"ok": True}
```

Update `decide_proposal` outcome recording for M8: in `app/proposals.py`, at the end of the APPLIED branch, add before `return`:

```python
    src = p.get("source", {})
    if src.get("kind") == "cross_proposal" and p.get("kind") == "confirm_return":
        cp = world.cross_proposals[src["cross_proposal_id"]]
        world.option_states[cp["option_id"]] = "DONE"
        world.outcomes.append({"option_id": cp["option_id"], "org_id": p["org_id"],
                               "days_protected": cp["days_protected"], "value_gbp": cp["value_gbp"]})
```

```python
# scripts/dump_fixtures.py
"""Write API responses for each demo user to tests/fixtures/ so the UI can be built against them."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)
out = Path("tests/fixtures")
out.mkdir(parents=True, exist_ok=True)
c.post("/api/demo/reset")
for user in ("dan", "priya", "marcus", "sam"):
    h = {"X-User-Id": user}
    data = {"me": c.get("/api/me", headers=h).json(), "sites": c.get("/api/sites", headers=h).json(),
            "sync_board": c.get("/api/sync-board", headers=h).json(), "city": c.get("/api/city", headers=h).json(),
            "links": c.get("/api/links", headers=h).json(), "cross": c.get("/api/cross-proposals", headers=h).json()}
    if data["sites"]:
        sid = data["sites"][0]["id"]
        data["timeline"] = c.get(f"/api/sites/{sid}/timeline", headers=h).json()
        data["labour"] = c.get(f"/api/sites/{sid}/labour", headers=h).json()
    (out / f"{user}.json").write_text(json.dumps(data, indent=2))
print("fixtures written to", out)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest -v`
Expected: all tests PASS. Then `uv run python scripts/dump_fixtures.py` writes 4 files.

- [ ] **Step 5: Commit**

```bash
git add app/main.py app/proposals.py app/network.py scripts/dump_fixtures.py tests/test_api.py tests/fixtures
git commit -m "feat: FastAPI routes, demo reset, fixtures"
```

---

### Task 11: Neo4j mirror, Cypher propagation and swap search (parity)

**Files:**
- Create: `app/graph_neo4j.py`, `.mcp.json`
- Test: `tests/test_neo4j_parity.py`

**Interfaces:**
- Consumes: `World`, `forward_pass`, `swap_candidates`.
- Produces: `Neo4jMirror(uri, user, password)` with `.sync(world)`, `.propagate(site_id, mode) -> dict[str, tuple[int,int]]`, `.swap_candidates(sub_org_id, home_site_id, trade, max_km) -> list[dict]`, `.close()`. Wiring: when `STORE=neo4j`, `app/main.py` calls `mirror.sync(W())` after reset and after every APPLIED proposal (best effort; failure is logged, never breaks the request).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_neo4j_parity.py
import os
import pytest
from app.schedule import forward_pass
from seed.seed import build_world

pytestmark = pytest.mark.skipif(not os.getenv("NEO4J_URI") or not os.getenv("NEO4J_PASSWORD"),
                                reason="Neo4j not configured")

def test_cypher_propagation_matches_python():
    from app.graph_neo4j import Neo4jMirror
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    m = Neo4jMirror(os.environ["NEO4J_URI"], os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"])
    try:
        m.sync(w)
        assert m.propagate("A", "confirmed") == forward_pass(w, "A", "confirmed")
        cands = m.swap_candidates("SPARKS", "A", "mep", 10.0)
        assert any(c["step_id"] == "C-K3" and round(c["km"], 1) == 1.7 for c in cands)
    finally:
        m.close()
```

- [ ] **Step 2: Run test to verify it fails** (with `.env` filled)

Run: `uv run pytest tests/test_neo4j_parity.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.graph_neo4j'` (or SKIPPED if Neo4j not configured yet; configure it first).

- [ ] **Step 3: Write minimal implementation**

```python
# app/graph_neo4j.py
from neo4j import GraphDatabase

from app.domain import World


class Neo4jMirror:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()

    def close(self):
        self.driver.close()

    def sync(self, world: World) -> None:
        orgs = [{"id": o.id, "name": o.name, "type": o.type} for o in world.orgs.values()]
        sites = [{"id": s.id, "name": s.name, "org_id": s.org_id, "lat": s.lat, "lon": s.lon, "offset": s.offset}
                 for s in world.sites.values()]
        steps = [{"id": s.id, "site_id": s.site_id, "code": s.code, "trade": s.trade, "days": s.days,
                  "delay": s.delay_days, "risk": s.risk_days, "deps": s.deps} for s in world.steps.values()]
        crews = [{"id": c.id, "org_id": c.org_id, "trade": c.trade} for c in world.crews.values()]
        bookings = [{"id": b.id, "crew_id": b.crew_id, "step_id": b.step_id, "start": b.start, "end": b.end}
                    for b in world.bookings.values()]
        approvals = [{"sub": a.sub_org_id, "gc": a.gc_org_id, "setup": a.setup_days} for a in world.approvals]
        with self.driver.session() as s:
            s.run("MATCH (n) DETACH DELETE n")
            s.run("UNWIND $rows AS r CREATE (:Org {id:r.id, name:r.name, type:r.type})", rows=orgs)
            s.run("""UNWIND $rows AS r MATCH (o:Org {id:r.org_id})
                     CREATE (o)-[:RUNS]->(:Site {id:r.id, name:r.name, offset:r.offset,
                             loc: point({latitude:r.lat, longitude:r.lon})})""", rows=sites)
            s.run("""UNWIND $rows AS r MATCH (si:Site {id:r.site_id})
                     CREATE (si)-[:HAS_STEP]->(:Step {id:r.id, site_id:r.site_id, code:r.code, trade:r.trade,
                             days:r.days, delay:r.delay, risk:r.risk})""", rows=steps)
            s.run("""UNWIND $rows AS r UNWIND r.deps AS d MATCH (a:Step {id:r.id}), (b:Step {id:d})
                     CREATE (a)-[:DEPENDS_ON]->(b)""", rows=steps)
            s.run("""UNWIND $rows AS r MATCH (o:Org {id:r.org_id})
                     CREATE (o)-[:EMPLOYS]->(:Crew {id:r.id, trade:r.trade})""", rows=crews)
            s.run("""UNWIND $rows AS r MATCH (c:Crew {id:r.crew_id}), (st:Step {id:r.step_id})
                     CREATE (c)-[:HAS_BOOKING]->(:Booking {id:r.id, start:r.start, end:r.end})-[:FOR_STEP]->(st)""",
                  rows=bookings)
            s.run("""UNWIND $rows AS r MATCH (a:Org {id:r.sub}), (g:Org {id:r.gc})
                     CREATE (a)-[:APPROVED_AT {setup_days:r.setup}]->(g)""", rows=approvals)

    def propagate(self, site_id: str, mode: str = "confirmed") -> dict[str, tuple[int, int]]:
        extra = {"baseline": "0", "confirmed": "s.delay", "risk": "s.delay + s.risk"}[mode]
        def work(tx):
            tx.run(f"""MATCH (si:Site {{id:$site}})-[:HAS_STEP]->(s:Step)
                       SET s.p_start = si.offset, s.p_end = si.offset + s.days + {extra}""", site=site_id)
            for _ in range(60):
                shifted = tx.run(f"""MATCH (s:Step {{site_id:$site}})-[:DEPENDS_ON]->(d:Step)
                                     WITH s, max(d.p_end) AS ready
                                     WHERE ready > s.p_start
                                     SET s.p_start = ready, s.p_end = ready + s.days + {extra}
                                     RETURN count(s) AS n""", site=site_id).single()["n"]
                if shifted == 0:
                    break
            return {r["id"]: (r["a"], r["b"]) for r in tx.run(
                "MATCH (s:Step {site_id:$site}) RETURN s.id AS id, s.p_start AS a, s.p_end AS b", site=site_id)}
        with self.driver.session() as s:
            return s.execute_write(work)

    def swap_candidates(self, sub_org_id: str, home_site_id: str, trade: str, max_km: float) -> list[dict]:
        q = """MATCH (home:Site {id:$home}), (sub:Org {id:$sub})-[:EMPLOYS]->(c:Crew)-[:HAS_BOOKING]->(b:Booking)
                     -[:FOR_STEP]->(st:Step {trade:$trade})<-[:HAS_STEP]-(t:Site)<-[:RUNS]-(gc:Org)
               WHERE t.id <> home.id AND EXISTS { (sub)-[:APPROVED_AT]->(gc) }
               WITH t, st, c, gc, b, point.distance(home.loc, t.loc) / 1000.0 AS km
               WHERE km <= $max_km
               RETURN t.id AS site_id, st.id AS step_id, c.id AS crew_id, gc.id AS gc_id, km,
                      b.start AS start, b.end AS end
               ORDER BY km"""
        with self.driver.session() as s:
            return [dict(r) for r in s.run(q, home=home_site_id, sub=sub_org_id, trade=trade, max_km=max_km)]
```

```json
// .mcp.json  (Neo4j MCP for Claude Code during development; credentials come from the shell env)
{
  "mcpServers": {
    "neo4j": {
      "command": "uvx",
      "args": ["mcp-neo4j-cypher"],
      "env": {
        "NEO4J_URI": "${NEO4J_URI}",
        "NEO4J_USERNAME": "${NEO4J_USER}",
        "NEO4J_PASSWORD": "${NEO4J_PASSWORD}"
      }
    }
  }
}
```

(Write `.mcp.json` without the `//` comment line; JSON has no comments.)

Wire into `app/main.py`: add near the top

```python
import logging
import os

from app.config import STORE

MIRROR = None
if STORE == "neo4j":
    from app.graph_neo4j import Neo4jMirror
    MIRROR = Neo4jMirror(os.environ["NEO4J_URI"], os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"])


def mirror_sync():
    if MIRROR:
        try:
            MIRROR.sync(W())
        except Exception as e:  # noqa: BLE001
            logging.warning("neo4j sync failed: %s", e)
```

and call `mirror_sync()` at the end of `reset()` and in `decide()` when the result status is `APPLIED`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_neo4j_parity.py -v`
Expected: PASS (1 test) against Aura.

- [ ] **Step 5: Commit**

```bash
git add app/graph_neo4j.py app/main.py .mcp.json tests/test_neo4j_parity.py
git commit -m "feat: Neo4j mirror with Cypher propagation and swap search, parity test, MCP config"
```

---

### Task 12: UI (Codex, or Claude if Codex is unavailable)

**Files:**
- Create: `static/index.html`

**Interfaces:**
- Consumes: the API in Task 10 (fixtures in `tests/fixtures/*.json` for offline work).
- Produces: one page, no build step.

**Screens (top to bottom):**
1. **Header:** "SiteSync" + user switcher (`GET /api/users`; stores `X-User-Id` in `localStorage`) + "Reset demo" (`POST /api/demo/reset`). Show role and company.
2. **Portfolio (PM/site manager):** one status bar per site from `GET /api/sites`: grey baseline bar (start → baseline_finish), coloured confirmed bar, striped risk extension, `+N days` badge. Click → timeline.
3. **Update panel (site manager/PM):** textarea + "Propose" (`POST /api/ingest/text`), "Sync from Plaud" (`POST /api/ingest/plaud`). Show each proposal: source excerpt; change `J1 finish 230 → 235`; knock-on (`N steps move`, `handover 397 → 402`); **labour impact** list (created/resolved imbalances as "M&E surplus: 6 workers, days 230–235"); buttons Confirm / Reject (`POST /api/proposals/{id}/decide`). Show "Waiting for PM" when status is `SITE_CONFIRMED`. Also list pending proposals from `GET /api/proposals?site_id=`.
4. **Sync Board (PM):** `GET /api/sync-board`. Each gap: type, trade, crew, days, warning days countdown, idle cost. Options ranked: title, feasible or reason, start-by day, days protected, value £, "Needs link" badge with a **Request link** button (`POST /api/links` with `target_anon_id`), **Approve** button for feasible ones (`POST /api/options/approve`). Footer: total days protected. State the assumptions on screen: "£8,000/day delay cost and £1,200 crew-day are demo assumptions; no-action model: crew returns 3 days late."
5. **City view:** `GET /api/city` as cards: area, distance band, phase, trade windows by week (need vs surplus). "Request link" button.
6. **Links and proposals:** `GET /api/links` (incoming requests: Accept with a simple pool terms form: trades, return guarantee checkbox) and `GET /api/cross-proposals` (Accept/Decline).
7. **Timeline:** SVG Gantt for the selected site (`GET /api/sites/{id}/timeline`): per step a grey baseline bar and a coloured confirmed bar; critical steps in red outline; risk flag icon; "today" line at day 220.
8. **Footer:** AI calls and providers from `GET /api/llm/log`.

- [ ] **Step 1:** Build the page against `tests/fixtures/priya.json` (open with `?fixture=priya` to read the fixture instead of the API).
- [ ] **Step 2:** Switch to the live API; run `uv run uvicorn app.main:app --reload`; walk through PRD §7 as Dan → Priya → Marcus → Sam → Marcus → Priya.
- [ ] **Step 3:** Verify: Priya never sees "Bow Wharf" or "Riverside" before the link is active; Dan sees only Site A.
- [ ] **Step 4:** Commit: `git add static/index.html && git commit -m "feat: UI for demo story"`.

---

### Task 13: Deploy on Crusoe (fallback: any Ubuntu VM)

**Files:**
- Create: `deploy/sitesync.service`, `docs/deploy.md`

- [ ] **Step 1:** Create the VM (console: Compute → Instances → Create; or CLI):

```bash
brew install crusoecloud/cli/crusoe && crusoe config init
crusoe compute vms create --name sitesync --type c1a.2x --location us-east1-a \
  --image ubuntu22.04:latest --keyfile ~/.ssh/id_ed25519.pub
crusoe networking vpc-firewall-rules create --name allow-web --action ALLOW --destination-ports 80 \
  --destinations <VM_PRIVATE_IP>/32 --protocols tcp --source-ports 1-65535 --sources 0.0.0.0/0 \
  --direction INGRESS --vpc-network-id <VPC_ID>
```

- [ ] **Step 2:** On the VM:

```bash
sudo apt-get update && sudo apt-get install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh && source ~/.local/bin/env
git clone <REPO_URL> sitesync && cd sitesync && uv sync
scp .env ubuntu@<VM_PUBLIC_IP>:~/sitesync/.env   # run this from your laptop
```

- [ ] **Step 3:** Service file:

```ini
# deploy/sitesync.service
[Unit]
Description=SiteSync
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/sitesync
ExecStart=/home/ubuntu/.local/bin/uv run uvicorn app.main:app --host 0.0.0.0 --port 80
AmbientCapabilities=CAP_NET_BIND_SERVICE
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo cp deploy/sitesync.service /etc/systemd/system/ && sudo systemctl enable --now sitesync
curl -s -H "X-User-Id: priya" http://<VM_PUBLIC_IP>/api/sites | head
```

Expected: JSON list with sites A and B.

- [ ] **Step 4:** Commit `deploy/` and `docs/deploy.md` (IP, commands used).

---

## Self-review

- **Spec coverage:** backbone (T1–T2), labour balance (T3), mechanisms M1/M3/M8/M10 with feasibility, deadlines, days protected (T4), link/pool/cross-proposals (T5), proposals with knock-on and option-B confirmation (T6), ingestion with Crusoe → OpenRouter → deterministic chain and Plaud (T7), signals (T8), visibility and anonymisation (T9), API (T10), Neo4j (T11), UI (T12), hosting (T13). Deferred per PRD S/L: Excel/photo ingestion, company risk check, M2/M4–M7/M9/M11/M12, minimum-crowd rule, auth.
- **Known simplification:** the event log is in-memory (`World.events`) and the Neo4j mirror is rebuilt on each confirmation (≈1k nodes, fine for the demo).
