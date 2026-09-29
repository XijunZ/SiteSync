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
    lag_days: int = 0  # start shift: start = natural start + lag (timeline edits)
    pause_start: int | None = None  # blocked window [pause_start, pause_start + delay_days) inside the step
    pause_reason: str | None = None


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
    offer_id: str | None = None  # the offer the borrower asked for (spec §5.7)
    target_step_id: str | None = None  # borrower's step the crew would work on
    created_at: str | None = None
    decided_at: str | None = None


@dataclass
class Offer:
    id: str
    gap_id: str
    org_id: str  # lender
    site_id: str
    crew_id: str
    step_id: str
    trade: str
    workers: int
    start: int
    end: int
    area: str
    status: str = "OPEN"  # OPEN | REQUESTED | TAKEN | WITHDRAWN | EXPIRED
    created_at: str | None = None
    need_id: str | None = None


@dataclass
class Need:
    """A borrower's anonymised request for capacity (trade, workers, window, area)."""
    id: str
    gap_id: str
    org_id: str  # borrower
    site_id: str
    step_id: str
    trade: str
    workers: int
    start: int
    end: int
    area: str
    status: str = "OPEN"  # OPEN | MATCHED | REQUESTED | AGREED | DONE | WITHDRAWN
    created_at: str | None = None
    offer_id: str | None = None


@dataclass
class ViewGrant:
    id: str
    site_id: str
    owner_org: str
    viewer_org: str
    requested_by: str
    status: str = "REQUESTED"  # REQUESTED | GRANTED | DECLINED | REVOKED
    created_at: str | None = None
    decided_at: str | None = None


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
    offers: dict = field(default_factory=dict)
    needs: dict = field(default_factory=dict)
    view_grants: dict = field(default_factory=dict)
    notifications: list = field(default_factory=list)
    risks: dict = field(default_factory=dict)  # step_id -> {days, kind, detail}
    seq: int = 0
    clock_min: int = 7 * 60 + 40  # demo clock: 07:40, advances with each event

    def tick(self, minutes: int = 3) -> str:
        self.clock_min += minutes
        return f"{self.clock_min // 60:02d}:{self.clock_min % 60:02d}"

    def now(self) -> str:
        return f"{self.clock_min // 60:02d}:{self.clock_min % 60:02d}"

    def notify(self, user_ids, text: str, ref: str | None = None) -> None:
        at = self.now()
        for uid in ([user_ids] if isinstance(user_ids, str) else user_ids):
            self.notifications.append({"id": self.next_id("n"), "to_user": uid, "text": text, "at": at,
                                       "read": False, "ref": ref})

    def pms_of(self, org_id: str) -> list[str]:
        return [u.id for u in self.users.values() if u.org_id == org_id and u.role == "PM"]

    def users_of(self, org_id: str) -> list[str]:
        return [u.id for u in self.users.values() if u.org_id == org_id]

    def next_id(self, prefix: str) -> str:
        self.seq += 1
        return f"{prefix}-{self.seq}"

    def log(self, type_: str, user_id: str | None, site_id: str | None, payload: dict,
            source: dict | None = None) -> dict:
        org_id = payload.pop("_org", None) if isinstance(payload, dict) else None
        if org_id is None:
            if user_id and user_id in self.users:
                org_id = self.users[user_id].org_id
            elif site_id and site_id in self.sites:
                org_id = self.sites[site_id].org_id
        ev = {"id": self.next_id("ev"), "type": type_, "user_id": user_id, "site_id": site_id,
              "org_id": org_id, "at": self.tick(), "payload": payload, "source": source or {"kind": "system"},
              "version": self.versions.get(site_id) if site_id else None}
        self.events.append(ev)
        return ev
