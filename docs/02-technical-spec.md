# SiteSync: Technical Specification (v2)

| | |
|---|---|
| Status | Draft v2 for review. Replaces v1. |
| Date | 2026-09-29 |
| Implements | `01-product-requirements.md` v2 (MVP = §7 there) |
| Owners | Claude Code: backbone, engine, ingestion core, API, seed, tests. Codex: UI, vision/photo, company risk check, README. |

## 1. Architecture

Event-driven. Every trigger runs the same pipeline; recompute is per affected site and takes milliseconds.

```
TRIGGERS                  INGESTION                        CORE                                  SURFACES
────────                  ─────────                        ────                                  ────────
Plaud note ─┐        ┌─ read format (text/rows/table/img)                                        Sync Board
Typed edit ─┼─► L0 ─►│  match entities (vocabulary)  ─► L1 candidates ─► L2 proposed changes      Timelines (own)
Excel/photo ┘ evidence└─ fill fields (LLM, schema)        (+ knock-on: dates AND labour)          Labour balance
                                                                  │ confirm (role rules)          City view (anon)
Weather / incidents ─► risk flags (scoped) ───────────────┐       ▼                               Links & pools
Clock (staleness, deadlines) ─► questions / expiry ───────┤  L3 EVENT LOG (append-only)           Sub planner view
Counterparty replies ─► proposal state ───────────────────┤       ▼ rebuild
                                                          └► L4 STATE: baseline · confirmed forecast
                                                                     · risk-adjusted forecast · snapshots
                                                                  ▼
                                                             L5 labour balance → gaps → options (mechanisms)
                                                                  ▼
                                                             L6 actions: approvals · links · proposals · outcomes
```

**Design rules**
1. **One path for every input.** Voice, typing, files and photos all become proposed changes with a source, and pass the same validation and knock-on preview.
2. **Only confirmed facts move the confirmed forecast.** Signals only move the risk-adjusted forecast.
3. **Events are the source of truth.** State is rebuilt from events; every confirmation creates a forecast version (snapshot).
4. **Visibility is enforced in one module (`views.py`).** Every API response and every LLM prompt that involves another company goes through it.
5. **Each company's data changes only through its own confirmation.**

## 2. Modules and ownership

| Module | Owner | Responsibility |
|---|---|---|
| `app/schemas.py` | Claude (shared contract) | Pydantic models for API and domain |
| `app/store.py` | Claude | `GraphStore` protocol; `get_store()` (`STORE=neo4j\|memory`) |
| `app/graph_neo4j.py` | Claude | Neo4j implementation (all Cypher) |
| `app/graph_memory.py` | Claude | In-memory implementation (tests, fallback) |
| `app/events.py` | Claude | Event types, append, rebuild, snapshots |
| `app/schedule.py` | Claude | Propagation (confirmed and risk-adjusted), critical path |
| `app/labour.py` | Claude | Demand, supply, balance, balance diff |
| `app/sync_engine.py` | Claude | Gap detection, mechanism catalogue, feasibility, scoring, lifecycle |
| `app/network.py` | Claude | Links, pools, cross-company proposals |
| `app/views.py` | Claude | Role scopes, anonymisation, redaction |
| `app/ingest.py` | Claude | Pipeline: read → match → fill → validate → proposals |
| `app/llm.py`, `app/prompts.py` | Claude | Crusoe client; extraction prompts |
| `app/plaud.py` | Claude | Plaud CLI wrapper |
| `app/signals.py` | Claude | Open-Meteo weather → risk flags; incident signal (manual trigger for demo) |
| `app/main.py` | Claude | FastAPI routes |
| `app/vision.py` | Codex | Whiteboard photo → bookings via OpenRouter (S) |
| `app/company_check.py` | Codex | Brave news check on a counterparty (S) |
| `static/index.html` | Codex | UI (vanilla JS + SVG), role switcher |
| `seed/` | Claude | CSV → 4 sites, labour loading, crews, bookings, network |
| `tests/` | Both | Engine (Claude), UI fixtures and vision/company check mocks (Codex) |

## 3. Data model

### 3.1 Graph (Neo4j labels; memory store mirrors the same properties)

```
(:Org {id, name, type: GC|SUB|AGENCY})
(:User {id, name, role: SITE_MANAGER|PM|OPS_DIRECTOR|SUB_PLANNER|OPERATOR, org_id, site_ids[]})
(:Site {id, name, org_id, loc: point, day_value, publish_to_network: bool, confidential: bool})
(:Step {id, site_id, code, name, trade, kind, days, weather_sensitive, risk_note,
        headcount,                                   // labour loading (planned workers/day)
        base_start, base_end,                        // baseline
        conf_start, conf_end, delay_days,            // confirmed forecast
        risk_start, risk_end})                       // risk-adjusted forecast
(:Crew {id, org_id, trade, size, name})
(:Booking {id, crew_id, step_id, start, end, status: PLANNED|CONFIRMED, source})
(:Link {id, org_a, org_b, status: REQUESTED|ACTIVE|DECLINED|REVOKED, requested_by, purpose})
(:Pool {id, link_id, trades[], equipment[], recharge, return_guarantee, priority_rule, notice_days})

(:Org)-[:RUNS]->(:Site)-[:HAS_STEP]->(:Step)-[:DEPENDS_ON]->(:Step)
(:Org)-[:EMPLOYS]->(:Crew)-[:HAS_BOOKING]->(:Booking)-[:FOR_STEP]->(:Step)
(:Org {type:SUB})-[:APPROVED_AT {since, setup_days}]->(:Org {type:GC})
(:Org)-[:LINKED {link_id}]->(:Org)
```

Integer working days on a global axis; `end` exclusive; `TODAY = 220`.

### 3.2 Event log (L3)

`{id, type, at, user_id, org_id, site_id, payload, source: {kind: voice|typed|excel|photo|signal|system, evidence_id, excerpt}, forecast_version}`

Types: `ProgressReported · ForecastFinishChanged · BlockerRaised · BlockerResolved · ReadinessReported · HeadcountReported · BookingAdded · BookingChanged · BookingCancelled · RiskFlagRaised · RiskFlagCleared · Rebaselined · OptionApproved · OptionDismissed · LinkRequested · LinkAccepted · LinkDeclined · PoolAgreed · ProposalSent · ProposalAccepted · ProposalDeclined · OutcomeRecorded · VocabularyLearned`

Stored in-process (list + JSON file) for today; Neo4j holds current state. Snapshots: after each confirmation, store `{version, site_id, step_id → (conf_start, conf_end)}`.

### 3.3 Proposed change (L2)

`{id, site_id, created_by, based_on_version, changes: [{step_id, field, from, to}], source, status: PENDING|ACCEPTED|REJECTED|SUPERSEDED, needs_pm: bool, knock_on: {dates, labour_diff}}`

### 3.4 Evidence (L0)

Raw transcript, file or typed text with timestamp; private to the org. Local disk under `data/evidence/{org_id}/` today.

## 4. Seed (MVP)

- Programme: on-site rows F–L from the CSV (52 steps); drop dependencies on earlier phases; **add K3 → J6**.
- **Labour loading defaults** (workers/day): demolition 6, groundworks 6, concrete 5, piling 4, rc_frame 8, roofing 4, glazing 4, cladding 5, scaffolding 4, bricklaying 5, mep 6, drylining 5, carpentry 4, finishes 4, lifts 3, landscaping 4, asbestos 4, ground_investigation 3. Non-crew owners (council, building control, utilities, milestone, developer, GC, surveyor): 0.
- Trade normalisation: as spec v1 §4.2 (unchanged).

| Site | Name | Org | Loc (lat, lon) | Offset | On day 220 |
|---|---|---|---|---|---|
| A | Hackney Wick Yard | Northgate | 51.5433, −0.0243 | 12 | Roof J1 starts (220–230) |
| B | Stratford Mill | Northgate | 51.5417, −0.0036 | 100 | Pile caps G5 |
| C | Bow Wharf | Riverside | 51.5282, −0.0183 | 7 | First fix K3 starts 225 |
| D | Canning Town Works | Riverside | 51.5147, 0.0080 | 185 | Demolition F7 |

- **Crews and bookings:** one crew per (GC, trade) for GC-direct trades. **Sparks Electrical** (SUB): crew S1 (6) booked on A-K3 (230–250) and A-K4; crew S2 (6) booked on C-K3 (225–245) and C-K4. **Voltline** (SUB, M&E): booked on K5 (risers) on all sites. Sparks is `APPROVED_AT` both Northgate and Riverside. One agency "CrewNow" `APPROVED_AT` Northgate.
- Users: Dan (SITE_MANAGER, Northgate, A), Priya (PM, Northgate, A+B), Marcus (PM, Riverside, C+D), Sam (SUB_PLANNER, Sparks), Ops (OPERATOR).
- No link between Northgate and Riverside at seed time (the demo creates it).

## 5. Core algorithms

### 5.1 Propagation (`schedule.py`)
For the confirmed forecast (and separately risk-adjusted, including active risk flags): forward pass in topological order per site. `start = max(own start, max(pred.end))`, `end = start + days + delay_days`. Neo4j: iterative Cypher inside one write transaction until no rows change (≤ 50 iterations); memory: topological forward pass. Critical path: backward pass; total float = 0.

### 5.2 Labour balance (`labour.py`)
- **Demand:** for each crew-bearing step, `headcount` workers on each day in [start, end) of the chosen forecast.
- **Supply:** for each booking, crew `size` on each day in [booking.start, booking.end).
- **Per booking:** surplus days = booking days where its step isn't active; shortage days = step-active days not covered by any booking for that step.
- **Clash:** the same crew with overlapping bookings whose steps are both active on the same day.
- **Balance diff:** compare before and after (proposed vs confirmed): list **created**, **resolved** and **changed** imbalances.
- **Lookahead:** gaps are raised within `[TODAY, TODAY + 20)`; imbalances beyond are listed as "later" in the diff but not raised.
- **Rule for the delayed step's own booking:** when a change extends a step, its booking is proposed as extended too ("extension assumed; confirm with sub").

### 5.3 Gap detection (`sync_engine.py`)
`Gap {id, type: SURPLUS|SHORTAGE|CLASH, site_id, step_id, crew_id, trade, start, end, workers, warning_days = start − TODAY, created_by_event}`

### 5.4 Mechanisms (`sync_engine.py`)
Each mechanism is a class with `applies_to(gap)`, `preconditions(gap, graph) → [ok|reason]`, `setup_days`, `parties`, `simulate(gap) → effect`, `steps` (lifecycle tasks).

| Mechanism | Applies to | Preconditions (MVP) | Setup days |
|---|---|---|---|
| M1 Resequence | SURPLUS | Unstaffed, ready step of the same trade on the same site in the window | 0 |
| M3 Re-slot trades | any | Always; moves bookings to new dates and checks for new clashes | 0 |
| M8 Slot swap | SURPLUS | Same sub has a booking on another site (any org) with its step active in the window; ≤ 10 km; **link ACTIVE with that org, or operator-run**; crew return ≤ its home step's new start | 1 |
| M10 Agency top-up | SHORTAGE | Agency `APPROVED_AT` the site's GC with the trade | 1 |

**Feasibility:** `setup_days ≤ warning_days` and all preconditions ok. Infeasible options are still returned, with `reason` (e.g. "M1: no unstaffed ready M&E work; K5 is staffed by Voltline").

**Scoring:** `days_protected = no_action_finish − with_action_finish` (from propagation), `value = days_protected × day_value + idle_cost_avoided` (idle crew-days put to work × crew-day rate; M8 earns this, M3 does not, since M3 holds the crew idle), then reliability (M1/M3 high, M8 medium, M10 medium), then setup days. **Start-by deadline** = `gap.start − setup_days`.

**No-action model (assumption, parameterised):** for a SURPLUS gap on a critical step, if nothing is done, the sub redeploys the crew and it returns `RETURN_LAG = 3` days late. This is modelled as a delay on the home step. With M8 (return guarantee) or M3 (booking held), no lag.

**Lifecycle:** `PROPOSED → APPROVED → IN_PROGRESS → CONFIRMED → DONE | FAILED | EXPIRED` (EXPIRED when TODAY > start-by deadline).

### 5.5 Expected demo numbers (verified by simulation; become tests)

| After confirming A-J1 +5 | Value |
|---|---|
| Steps moved on A | 18, each +5 (J6, K3, K4, K6–K15, L2, L4–L7) |
| A handover (L7 end) | 397 → 402 |
| Gaps within lookahead (all sites) | exactly 1: **SURPLUS, Sparks S1, A-K3, M&E, days 230–235, 6 workers** |
| Other sites | unchanged |
| No action (return lag 3) | A handover 405 (+8 vs baseline) |
| With M8 or M3 | 402 (+5) → **3 days protected × Northgate day value** |
| M1 | infeasible: K5 staffed by Voltline |
| M8 target | C-K3 (225–245), Sparks S2 active; A to C 1.7 km; needs link Northgate ↔ Riverside |

### 5.6 Anonymisation (`views.py`)
City view projection of another org's published, non-confidential sites: `{anon_id (hash), area: "E London grid ~1 km", project_type, phase (from the active step's CSV phase), trade windows by week: [{trade, need|surplus, week_from, week_to}]}`. No names, codes, exact dates or coordinates. Minimum-crowd rule: parameter `MIN_CROWD = 3`; **disabled for the demo** (4 sites) and stated as such.

### 5.7 Link and pool (`network.py`)
`request_link(from_org, anon_id, purpose)` → the target org's PMs see the requester's name and purpose → `accept` creates Link ACTIVE and a Pool (terms form) → M8 preconditions between the two orgs are satisfied. Proposals: `ProposalSent` to the counterparty PM and the sub planner → each accepts → each GC gets a **proposed change** (booking change) in its own review → confirmed separately.

### 5.8 Confirmation rules
The site manager confirms facts. `needs_pm = true` when the change moves a critical-path step by ≥ 2 days or moves the site's finish date. Until the PM approves, the change shows as "confirmed by site, pending PM".

## 6. Ingestion (`ingest.py`)

1. **Read:** text (Plaud transcript / typed / pasted) directly; Excel via `openpyxl` (S); photo via `vision.py` (S).
2. **Match entities:** vocabulary per site (step names, codes, synonyms such as "roof, roofing, membrane" → J1; sub names and nicknames). The LLM receives the site's step catalogue (code, name, trade, status) and must choose from it.
3. **Fill fields:** Crusoe `openai/gpt-oss-120b`, output validated against pydantic `ExtractedUpdate {site_id, step_code | candidates[], field, value, reason, confidence, excerpt}`. Try `response_format` json_schema → fall back to json_object → fall back to prompt-only JSON; validate; one retry with the validation error.
4. **Validate:** against the graph (e.g. finish ≥ predecessors' finish, delay 1–60 days).
5. **Propose:** build L2 proposed change with knock-on (dates + labour diff).
6. **Demo safety:** if all LLM calls fail, return a canned extraction for the exact demo transcript, marked `source: fallback`.

## 7. Integrations (researched 2026-09-29)

| Tool | Use | How | Gotchas and mitigations |
|---|---|---|---|
| **Neo4j Aura Free** | Backbone graph, network, propagation, geo distance | Python driver 6.x (`AsyncGraphDatabase`, one driver per app lifespan, `execute_query` / managed write tx); `point()` + `point.distance`; quantified paths for sub-tier chains | One Free instance per account; ~200k nodes / 400k rels (we use ~1k); **pauses after 3 days idle**, so resume before judging; GDS not on Free |
| **Crusoe inference** | Extraction (gpt-oss-120b, $0.05/$0.20 per 1M); optional alert wording (Kimi K2.6) | OpenAI SDK, `base_url=https://api.inference.crusoecloud.com/v1`, `CRUSOE_API_KEY` | **JSON-schema output, tools and streaming not documented** → fallback chain + pydantic; 30 RPM without a card; needs a non-prepaid card |
| **Crusoe compute** | Host the app | `c1a.2x` CPU VM (~$0.08/h), Ubuntu 22.04; `crusoe compute vms create ...` | Only SSH open by default: add firewall rule for 80/443 **to the private IP**; card required; quotas |
| **Plaud** | Capture voice notes | Plaud CLI (`plaud recent`, `plaud transcript <id>`), token in `~/.plaud/tokens.json`; poll every 30 s or a "Sync from Plaud" button | **Notes under ~5 min are not auto-transcribed**: tap "Generate" in the app; phone app records only with a Plaud device; transcript is text `[mm:ss] Speaker: text` (parse); fallback: paste transcript |
| **Open-Meteo** | Weather signal | `GET api.open-meteo.com/v1/forecast?latitude&longitude&daily=precipitation_sum,wind_speed_10m_max` | Free, no key. Demo can inject a signal via `POST /api/signals` for reproducibility |
| **OpenRouter** (S) | Whiteboard photo → bookings | `google/gemini-3.8-flash`, base64 data URL, `response_format` json_schema + `provider.require_parameters: true`, `data_collection: deny` | Strict schema needs `additionalProperties: false`; validate with pydantic |
| **Brave Search** (S) | Company risk check on a counterparty | `GET /res/v1/news/search`, `X-Subscription-Token`, `freshness=py` | Don't store raw results (ToS): keep the summary and URLs; attribution required on free credits; small firms have little news |

## 8. API (FastAPI, JSON, snake_case)

Caller identity: header `X-User-Id` (demo role switcher; no auth). Every response passes through `views.py`.

```
GET  /api/me                                   → user, role, org, scopes
GET  /api/sites                                → own sites: status bars (baseline, confirmed, risk-adjusted finish, variance)
GET  /api/sites/{id}/timeline                  → steps with base/conf/risk dates, critical flag, bookings
GET  /api/sites/{id}/labour?from&to            → balance per trade per day
POST /api/ingest/text      {site_id, text}     → proposed change (L2) with knock-on
POST /api/ingest/plaud     {site_id, file_id?} → same (latest recording if no id)
GET  /api/plaud/recordings                     → recent recordings
POST /api/ingest/excel     multipart (S)       → proposed booking changes
POST /api/ingest/photo     multipart (S)       → proposed booking changes
GET  /api/proposals?site_id                    → pending proposed changes
POST /api/proposals/{id}/decide {accept|reject, edits?} → events; returns new version + gaps
POST /api/signals          {type, site_ids|loc+radius, window, severity}  → risk flags (demo trigger)
POST /api/signals/weather/refresh              → Open-Meteo pull
GET  /api/sync-board                           → gaps (own org) with ranked options, syncs in flight, outcomes
POST /api/options/{id}/approve                 → mechanism lifecycle start
GET  /api/city                                 → anonymised projects in the city
POST /api/links            {anon_id, purpose}  → link request
POST /api/links/{id}/decide {accept|decline, pool_terms?}
GET  /api/links                                → own links and pools
GET  /api/cross-proposals                      → proposals involving my org / my crews
POST /api/cross-proposals/{id}/decide {accept|decline}
GET  /api/events?site_id                       → audit trail
POST /api/demo/reset                           → reseed
```

Errors: `{error, detail}` with 4xx/5xx.

## 9. Security and visibility

- `views.py` builds every response from the caller's scope: own org full; linked org pool only; others anonymised; sub planner own bookings only.
- LLM prompts include only the caller org's data.
- **Test:** for each user, serialise every API response and assert no other org's site id, site name, step code or user name appears (except the requester's name on link requests, and counterparts after mutual acceptance).

## 10. Testing

| Test | Asserts |
|---|---|
| `test_seed` | 4 × 52 steps; K3→J6; headcounts; bookings as §4; Sparks approved at both GCs |
| `test_propagation` | §5.5 dates; other sites unchanged; idempotent |
| `test_labour` | Before change: no gaps in lookahead. After: exactly the one SURPLUS gap in §5.5 |
| `test_mechanisms` | M1 infeasible with reason; M3 and M8 feasible (M8 only after link); days protected = 3; start-by deadlines |
| `test_ingest` | Demo transcript → J1 +5 with mocked LLM; ambiguous input → candidates; validation blocks impossible dates |
| `test_confirmation` | `needs_pm` for finish-date moves; version increments; snapshot stored |
| `test_visibility` | §9 leak test for Dan, Priya, Marcus, Sam |
| `test_link_flow` | request → accept → pool → M8 becomes feasible → cross-proposal accept → each org confirms its own booking |
| `test_store_parity` | memory and Neo4j stores agree (skipped without Neo4j) |

## 11. Build plan (today)

| By | Claude | Codex | You |
|---|---|---|---|
| 13:30 | schemas, seed, memory store, propagation, labour balance, tests green | UI skeleton with role switcher, against fixtures | Crusoe key, Aura instance, `plaud login`, record the demo note |
| 14:30 | sync engine (M1, M3, M8, M10), views, API core, fixtures published | Timelines, labour diff panel, Sync Board | Crusoe VM |
| 15:30 | ingest (Crusoe + Plaud), link and pool, cross-proposals, Neo4j store | City view, links, sub planner view | Test Plaud end to end |
| 16:30 | Weather signal, deploy to Crusoe, end-to-end run × 3 | Polish; photo (S) if time | Rehearse |
| 17:30 → | Fixes only | README | Record backup video, submit |

## 12. Changes from spec v1

Replaced: GC-neutral idle-crew matcher → sync engine with mechanisms; batch → event-driven with event log and snapshots; single forecast → baseline / confirmed / risk-adjusted; GC switcher → role and user switcher; neutrality → three-tier visibility with links and pools; OpenRouter/Brave demoted to optional; Plaud CLI gotchas and Crusoe fallback chain added.
