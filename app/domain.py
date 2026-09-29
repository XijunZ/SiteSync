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

    def log(self, type_: str, user_id: str | None, site_id: str | None, payload: dict,
            source: dict | None = None) -> dict:
        ev = {"id": self.next_id("ev"), "type": type_, "user_id": user_id, "site_id": site_id,
              "payload": payload, "source": source or {"kind": "system"},
              "version": self.versions.get(site_id) if site_id else None}
        self.events.append(ev)
        return ev
