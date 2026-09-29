# SiteSync: Technical Specification

| | |
|---|---|
| Status | Draft for review |
| Date | 2026-09-29 |
| Implements | `01-product-requirements.md` (US-1 to US-17) |
| Owners | Claude Code: engine, seed, schemas, API. Codex: UI, LLM, ingest, weather, README. |

Where this spec differs from the brief in `CLAUDE.md`, this spec wins once approved. Differences are listed in section 11.

## 1. Architecture

```
                    static/index.html  (vanilla JS + SVG, GC switcher)
                               │  JSON over HTTP
                               ▼
┌──────────────────────── app/main.py (FastAPI) ────────────────────────┐
│  routes  ──►  views.py (per-GC filtering and anonymisation)          │
│     │                                                                 │
│     ├──► ingest.py ──► llm.py ──► OpenRouter (OpenAI SDK)             │
│     │                    └── call log (model, tokens, cost, latency)  │
│     ├──► engine.py  (idle gaps, clashes, matching, critical path)     │
│     │        │                                                        │
│     │        ▼                                                        │
│     └──► store: GraphStore protocol                                   │
│              ├── Neo4jStore     (graph.py, Cypher, Aura Free)         │
│              └── NetworkxStore  (graph_nx.py, in-memory fallback)     │
└───────────────────────────────────────────────────────────────────────┘
                               ▲
                   seed/seed.py (CSV → 4 sites, crews)
```

Design rules:
- **All persistence and propagation goes through `GraphStore`.** Swapping Neo4j for networkx is one env var: `STORE=neo4j|memory`.
- **Neutrality is enforced in one place, `views.py`.** Engine outputs are complete. Views are the only thing routes return and the only thing fed to alert-writing prompts.
- **All LLM calls go through `llm.call()`.** That one function handles routing, fallback, retries and logging.

## 2. Module ownership and files

| File | Owner | Purpose |
|---|---|---|
| `app/schemas.py` | Claude (shared) | Pydantic models for all API payloads and domain objects. Change only with notice to the other agent. |
| `app/store.py` | Claude | `GraphStore` protocol and `get_store()` factory |
| `app/graph.py` | Claude | `Neo4jStore`: all Cypher lives here |
| `app/graph_nx.py` | Claude | `NetworkxStore`: same behaviour, in memory |
| `app/engine.py` | Claude | Idle gaps, clashes, matching, critical path (pure Python over store data) |
| `app/views.py` | Claude | Per-GC filtering and anonymisation |
| `app/main.py` | Claude | FastAPI routes, error handling, static files |
| `app/config.py` | Claude | Env loading, constants (TODAY, LOOKAHEAD, CREW_DAY_GBP) |
| `seed/seed.py`, `seed/programme.py` | Claude | CSV parsing, trade mapping, site and crew generation |
| `app/llm.py`, `app/prompts.py` | Codex | OpenRouter client, model routing, cost log |
| `app/ingest.py` | Codex | Transcript and photo extraction |
| `app/plaud.py` | Claude | Plaud CLI wrapper: list recent recordings, fetch polished transcript (subprocess, parsed text output) |
| `app/weather.py` | Codex | Open-Meteo lookup (Could) |
| `static/index.html` | Codex | UI |
| `tests/` | Claude (engine), Codex (ingest, mocked LLM) | pytest |

## 3. Data model

### 3.1 Graph (Neo4j labels; networkx uses the same properties on nodes)

```
(:GC   {id, name})
(:Site {id, name, gc_id, lat, lon, offset})
(:Step {id, site_id, code, name, trade, days, kind, weather_sensitive, risk,
        planned_start, planned_end, pred_start, pred_end, delay_days})
(:Crew {id, name, trade, gc_id})          gc_id = null for independent crews

(:GC)-[:RUNS]->(:Site)
(:Site)-[:HAS_STEP]->(:Step)
(:Step)-[:DEPENDS_ON]->(:Step)            finish-to-start, same site only
(:Step)-[:ASSIGNED_TO]->(:Crew)           0 or 1 per step
(:GC)-[:EMPLOYS]->(:Crew)                 both GCs EMPLOY each independent crew
```

- `id` for a step is `{site}-{code}`, e.g. `A-K3`.
- All times are integer **working days** on a global axis. Day 0 is the earliest site start.
- `end` is exclusive: a 10-day step starting on day 208 has `end = 218`.
- `delay_days` is the extra duration added by an update (default 0). Predicted duration is `days + delay_days`.

### 3.2 Constants (`app/config.py`)

| Name | Value | Why |
|---|---|---|
| `TODAY` | 220 | Fixed so the demo is reproducible |
| `LOOKAHEAD_DAYS` | 20 | Four working weeks, a standard construction lookahead |
| `MIN_GAP_DAYS` | 3 | Gaps of 2 days or fewer are not worth alerting |
| `MIN_MATCH_OVERLAP` | 3 | An offer must cover at least 3 days of the other site's step |
| `MAX_MATCH_KM` | 10 | |
| `CREW_DAY_GBP` | 1200 | Stated on screen as an assumption |
| `PROPAGATION_MAX_ITER` | 50 | |

## 4. Seed data (`seed/`)

### 4.1 Programme

- Load `development_programme_seed.csv`. Keep rows whose `id` starts with F, G, H, J, K, L (52 steps).
- Drop dependencies on steps outside that set.
- **Add dependency `K3 → J6`** (M&E first fix needs the building weathertight). Without it, the demo delay has no downstream effect (PRD R1).
- Planned dates are computed by a forward pass (earliest start) from site start. Programme length is 385 days.

### 4.2 Trade normalisation

| `owner_or_trade` in CSV | `trade` | Crew? |
|---|---|---|
| Groundworks; Groundworks, concrete | `groundworks` | yes |
| Concrete | `concrete` | yes |
| Demolition; Demolition, haulage | `demolition` | yes |
| Licensed asbestos contractor | `asbestos` | yes |
| Specialist contractor | `ground_investigation` | yes |
| Piling contractor | `piling` | yes |
| RC frame | `rc_frame` | yes |
| Roofing | `roofing` | yes |
| Glazing | `glazing` | yes |
| Cladding | `cladding` | yes |
| Scaffolding | `scaffolding` | yes |
| Bricklaying | `bricklaying` | yes |
| Mechanical and electrical | `mep` | yes |
| Drylining | `drylining` | yes |
| Fit-out carpentry | `carpentry` | yes |
| Painting, flooring | `finishes` | yes |
| Lift contractor | `lifts` | yes |
| Landscaping | `landscaping` | yes |
| Surveyor, Council, Utility companies, Building control, General contractor, Developer, Milestone | as-is, lower snake case | **no** |

An unknown value fails the seed loudly.

### 4.3 Sites

| Site | Name | GC | Lat, lon | Start offset | Stage on day 220 |
|---|---|---|---|---|---|
| A | Hackney Wick Yard | Northgate Build (`NG`) | 51.5433, −0.0243 | 12 | Roof waterproofing J1 starts (days 220–230) |
| B | Stratford Mill | Northgate Build (`NG`) | 51.5417, −0.0036 | 100 | Pile caps G5 |
| C | Bow Wharf | Riverside Construction (`RV`) | 51.5282, −0.0183 | 7 | Blockwork done, M&E first fix K3 starts day 225 |
| D | Canning Town Works | Riverside Construction (`RV`) | 51.5147, 0.0080 | 185 | Structural demolition F7 |

All sites are within 4 km of each other. A to C is 1.7 km.

### 4.4 Crews

- One crew per `(GC, trade)` for every crew-bearing trade: id `{GC}-{trade}`, e.g. `NG-mep`.
- Two independent crews: `IND-mep` and `IND-drylining`, employed by both GCs.
- Assignment: every crew-bearing step goes to its GC's crew, **except** K5 (risers and plant room) → `IND-mep` and K9 (drylining, upper floors) → `IND-drylining` on all four sites.
- Result: A-K5 (230–250) and C-K5 (225–245) both use `IND-mep`, which is a planned clash for US-12.

## 5. Engine behaviour

### 5.1 Apply update

`apply_delay(step_id, delay_days)`: set `delay_days += n` and `pred_end = pred_start + days + delay_days`.

`apply_booking(...)` (US-11): create or replace an `ASSIGNED_TO` edge. The step's dates are not changed.

### 5.2 Propagate (Neo4j)

Loop until `shifted = 0` or 50 iterations. Only pushes later, never pulls earlier:

```cypher
MATCH (s:Step)-[:DEPENDS_ON]->(d:Step)
WHERE s.site_id = $site_id
WITH s, max(d.pred_end) AS ready
WHERE ready > s.pred_start
SET s.pred_start = ready,
    s.pred_end   = ready + s.days + coalesce(s.delay_days, 0)
RETURN count(s) AS shifted
```

The only difference from the brief is `+ delay_days`, so a step that is itself delayed keeps its delay when pushed.

networkx does the same with a topological-order forward pass.

### 5.3 Critical path

A backward pass over predicted dates computes latest finish. A step is `critical` when total float is 0. This runs in Python in `engine.py` on the step list from the store.

### 5.4 Idle gaps (new idle time only)

For each crew-assigned step `s` whose `pred_start > planned_start`:
- candidate window = `[planned_start, pred_start)`, clipped to `[TODAY, TODAY + LOOKAHEAD_DAYS)`
- remove days on which the same crew has any other predicted booking
- emit each remaining contiguous run of at least `MIN_GAP_DAYS` days as an `IdleGap {crew_id, gc_id, site_id, step_id, start, end, days}`

Idle time that already existed in the plan is ignored by design (PRD R2).

### 5.5 Clashes

A clash is a pair of steps on **different sites** assigned to the same crew whose predicted windows overlap and whose overlap intersects the lookahead. Output: `Clash {crew_id, step_a, step_b, start, end, days}`.

### 5.6 Matching

For each `IdleGap g`, consider steps `t` on other sites (any GC) where:
- `t.trade == crew.trade`
- overlap = `|[g.start, g.end) ∩ [t.pred_start, t.pred_end)|` is at least `MIN_MATCH_OVERLAP`
- distance between sites is at most `MAX_MATCH_KM` (Neo4j `point.distance`; haversine in networkx)

Rank by overlap descending, then distance ascending, then step code. Output: `Match {gap, step_id, overlap_days, distance_km, value_gbp = overlap_days × CREW_DAY_GBP}`.

### 5.7 Reset

Set `pred_start = planned_start`, `pred_end = planned_end` and `delay_days = 0` on all steps. Remove bookings added by photo ingest (marked `source = 'ingest'`).

### 5.8 Expected demo numbers (verified by simulation; these become tests)

| After applying A-J1 +5 | Value |
|---|---|
| Steps shifted on A | 18 (J6, K3, K4, K6–K15, L2, L4–L7), each +5 |
| A predicted finish (L7 end) | 397 → 402 |
| Other sites | unchanged |
| Idle gaps (whole system) | exactly 1: `NG-mep`, A-K3, days 230–235, 5 days |
| Top match | C-K3 (RV, `RV-mep`, 225–245), overlap 5, 1.7 km, £6,000 |
| Second match | C-K5 (`IND-mep`), overlap 5 (also shown, ranked second by code) |

## 6. Neutrality (`views.py`)

Every route that takes `gc` passes engine output through a view function. Rules:

| Object | Own GC sees | Other GC sees |
|---|---|---|
| Site, step, timeline | full | nothing |
| Idle gap | full | nothing directly |
| Match, gap owner side | own crew and gap in full; target as `{trade, window, distance_km, value_gbp}` only | n/a |
| Match, receiving side | own step in full; offer as "vetted {trade} crew available days X–Y, {km} km away" | n/a |
| Clash involving independent crew | own step in full; other step as `{"site": "another site", window}` if it is the other GC's | same, mirrored |

- Offers are identified by an opaque `offer_id` (a hash), never by a crew, site or step id from the other GC.
- **Prompt neutrality:** alert-writing prompts (US-13) receive only the output of the view function for that GC.
- **Test:** for each GC, serialise every API response and assert that no other-GC site id, site name, step id or GC name appears as a substring.

## 7. API contract

All JSON uses snake_case. Errors return `{"error": "<code>", "detail": "<message>"}` with 4xx or 5xx. The fields `gc_id` / `site_id` are validated against the caller's GC.

```
GET  /api/gcs                                   → [{id, name}]
GET  /api/sites?gc=NG                           → [{id, name, lat, lon, stage, planned_finish, pred_finish}]
GET  /api/timeline?gc=NG&site=A                 → {site, today, steps: [TimelineStep]}
POST /api/ingest/transcript  {gc_id, text}      → {proposals: [DelayProposal], candidates: [DelayProposal], llm_call_id}
GET  /api/plaud/recordings?days=1               → [{file_id, name, created_at, duration_s}]   (via Plaud CLI)
POST /api/ingest/plaud       {gc_id, file_id}   → same as ingest/transcript, plus {source: "plaud", file_id}
POST /api/ingest/photo       multipart: gc_id, file → {bookings: [BookingProposal], confidence, llm_call_id}
POST /api/updates/apply      {gc_id, delays: [DelayProposal], bookings: [BookingProposal]}
                                                → {shifted_steps, finish_change_days, alerts: AlertsView}
GET  /api/alerts?gc=NG                          → AlertsView
POST /api/demo/reset                            → {ok: true}
GET  /api/llm/log                               → {calls: [LlmCall], total_cost_usd}
```

Key schemas (`app/schemas.py`):

```python
class TimelineStep(BaseModel):
    id: str; code: str; name: str; trade: str; kind: Literal["task","approval","wait","milestone"]
    weather_sensitive: bool; risk: str | None
    planned_start: int; planned_end: int; pred_start: int; pred_end: int
    shift_days: int; critical: bool; crew_label: str | None   # "Northgate M&E" or "Independent subcontractor"

class DelayProposal(BaseModel):
    site_id: str; step_code: str; delay_days: int = Field(ge=1, le=60)
    reason: str; confidence: float = Field(ge=0, le=1)

class BookingProposal(BaseModel):
    site_id: str; trade: str; crew_name: str; start_day: int; end_day: int

class IdleGapView(BaseModel):
    crew_label: str; site_id: str; step_code: str; start: int; end: int; days: int; cost_gbp: int
    offers: list["OfferOut"]           # anonymised

class OfferOut(BaseModel):   offer_id: str; trade: str; start: int; end: int; overlap_days: int; distance_km: float; value_gbp: int
class OfferIn(BaseModel):    offer_id: str; trade: str; start: int; end: int; for_step_id: str; overlap_days: int; distance_km: float; value_gbp: int
class ClashView(BaseModel):  crew_label: str; own_step_id: str; other: str; start: int; end: int; days: int

class AlertsView(BaseModel):
    idle_gaps: list[IdleGapView]; incoming_offers: list[OfferIn]; clashes: list[ClashView]
    summary: str | None                # LLM-written (US-13); null if the LLM is unavailable

class LlmCall(BaseModel):
    id: str; purpose: str; provider: Literal["crusoe","openrouter","fallback"]; model: str; latency_ms: int; prompt_tokens: int; completion_tokens: int; cost_usd: float; ok: bool
```

Codex builds the UI against fixtures in `tests/fixtures/*.json`, which Claude generates from the real engine. Fixtures are available before the routes are finished.

## 8. LLM pipeline (Codex owns; interface fixed here)

```python
# app/llm.py
def call(purpose: str, messages: list, schema: type[BaseModel] | None, tier: Literal["cheap","strong","vision"]) -> BaseModel | str
```

- Two OpenAI-compatible providers through the same OpenAI SDK:
  - `crusoe`: `base_url=https://api.inference.crusoecloud.com/v1`, key `CRUSOE_API_KEY`. **Primary for text.** Required for the overall prizes.
  - `openrouter`: `base_url=https://openrouter.ai/api/v1`, key `OPENROUTER_API_KEY`. Vision, plus fallback for text.
- Models come from env as `provider:model` fallback lists (defaults in `.env.example`, verified 2026-09-29):
  - `MODEL_CHEAP`: `crusoe:openai/gpt-oss-120b`, then `openrouter:openai/gpt-oss-120b`
  - `MODEL_STRONG`: `crusoe:moonshotai/Kimi-K2.6`, then `openrouter:moonshotai/kimi-k2.6`
  - `MODEL_VISION`: `openrouter:google/gemini-3.8-flash`
- Crusoe's docs don't mention JSON-schema output, so use JSON mode plus pydantic validation for Crusoe, and `response_format` JSON schema for OpenRouter.
- `LlmCall` logs `provider` as well as `model`, so the UI can show Crusoe vs OpenRouter usage.
- Structured output with a JSON schema from pydantic. Validate, and retry once with the validation error on failure.
- Cost is taken from the OpenRouter usage response. Every call is appended to an in-memory log.
- **Transcript prompt input:** transcript text plus the caller GC's site list and step catalogue (code, name, trade). No other GC data.
- **Demo safety:** if every model fails, `ingest` returns a canned proposal for the exact demo transcript, flagged `"source": "fallback"` in the log.

## 9. Testing

| Test | Asserts |
|---|---|
| `test_seed.py` | 4 sites × 52 steps; the K3→J6 dependency exists; the day-220 stages match the table in 4.3; every crew-bearing step has exactly one crew |
| `test_propagation.py` | Numbers in 5.8: 18 shifted, finish +5, other sites unchanged; propagation is idempotent |
| `test_idle_gaps.py` | Before the delay: 0 gaps. After: exactly 1, `NG-mep` 230–235 |
| `test_matching.py` | Top match C-K3, overlap 5, about 1.7 km, £6,000 |
| `test_clashes.py` | A-K5 vs C-K5 on `IND-mep` reported |
| `test_neutrality.py` | No cross-GC leakage in any API response (section 6) |
| `test_reset.py` | Reset restores the seeded state exactly |
| `test_store_parity.py` | networkx and Neo4j give identical results for the above (skipped if Neo4j isn't configured) |
| `test_ingest.py` (Codex) | The demo transcript gives A/J1/+5 with a mocked LLM; ambiguous input returns candidates |

Engine tests run against `NetworkxStore` by default (fast, no network), and against Neo4j when `STORE=neo4j`.

## 10. Delivery plan

Branches: `main` (always demo-able), `claude/engine`, `codex/ui-llm`. Merge to `main` at every milestone.

| By | Claude Code | Codex |
|---|---|---|
| 10:45 | schemas.py, config, seed + NetworkxStore, propagation tests green. Push schemas to `main`. | Skeleton index.html against fixtures, llm.py call log |
| 12:30 | engine (gaps, clashes, matching, critical), views, all API routes, fixtures, Neo4jStore + parity | Timeline SVG, GC switcher, alerts panel |
| 14:30 | Harden, neutrality test, `/api/updates/apply` summary | Transcript ingest + confirm flow; photo ingest |
| 16:30 | End-to-end demo run 3× on Neo4j | UI polish, LLM footer, alert summary |
| 17:30 | Deploy (Vultr or Crusoe) | README: setup, demo script, sponsor usage |
| 19:00 | Rehearse, bug fixes only, backup video, final push | |

## 11. Changes from the brief (need approval)

1. Extra dependency K3 → J6 (PRD R1).
2. Idle gaps count only new idle time, inside a 20-day lookahead (PRD R2).
3. Trade normalisation table, with non-crew owners getting no crew (PRD R3).
4. Matching uses at least 3 days of overlap instead of "start inside the gap" (PRD R4).
5. API: request bodies carry `gc_id`; `timeline` takes `gc`; new `GET /api/gcs`; `apply` takes `delays` and `bookings` instead of a generic `updates`. Needed to enforce neutrality at the API boundary.
6. `delay_days` property added to Step so propagation preserves a step's own delay.
7. New modules: `store.py`, `graph_nx.py`, `engine.py`, `views.py`, `config.py`, `prompts.py`, `plaud.py`.
8. LLM inference is on Crusoe first, with OpenRouter for vision and fallback (the brief had OpenRouter only). This is required because Crusoe gates the overall prizes.
9. Plaud is integrated through the Plaud CLI (new routes `GET /api/plaud/recordings` and `POST /api/ingest/plaud`). Deployment moves from last priority to a smoke deploy on Crusoe by 12:30.

Once approved, update `CLAUDE.md` and `AGENTS.md` to point at `docs/` as the source of truth.
