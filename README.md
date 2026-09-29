# SiteSync

**SiteSync keeps construction sites in sync.** When one site slips, the crews, bookings and handovers that depend on it fall out of sync, across sites and across companies. SiteSync catches the knock-on early and puts the right fix in front of the project manager while there's still time to act.

Built at **The AI Conference Hack Day 2026** (Pier 48, San Francisco).

## The demo story

1. **Capture (Plaud).** Dan, the site manager at Hackney Wick Yard, records a 45-second site update on a Plaud device: the roofing supplier's second membrane batch failed its factory quality check, and the replacement takes five working days.
2. **Understand (Crusoe).** SiteSync pulls the recording from Dan's Plaud cloud library. An open-weight model on Crusoe (`gpt-oss-120b`) turns it into a structured change: *roof waterproofing blocked days 225–230, finish 230 → 235*. It ignores the rest of the update (windows, cladding, scaffold).
3. **Propagate (Neo4j).** The project is a dependency graph in Neo4j. The delay ripples J1 → J6 → K3 → … → handover: 18 steps move and handover slips 397 → 402. Nobody mentioned the electricians, but the graph shows that **Sparks Electrical's crew of 6 will be idle on days 230–235**, because first fix can't start until the roof is done.
4. **Decide (next-best-action engine).** Options are ranked by lead time. With no action, Sparks redeploys the crew and it returns 3 days late (handover 405). The PM, Priya, offers the idle days to nearby projects, anonymised.
5. **Match (across companies).** 1.7 km away, Marcus at Riverside's Bow Wharf is 6 M&E workers short. He requests capacity, and SiteSync matches him instantly. It's feasible because **Sparks already holds a subcontract on his site** (no onboarding, 10 working days' notice). Neither company sees the other's programme until both agree.
6. **Agree and prove.** Priya sets terms (crew back by day 235), Sparks accepts, and each GC confirms its own booking. Result: **3 days of handover protected (£24,000 at Northgate's day rate)**, £6,000 of idle crew cost avoided for Sparks, and Riverside covers its shortage without paying an agency premium.

## How each sponsor is used

| Sponsor | Role |
|---|---|
| **Plaud** | Capture. Site updates recorded on a Plaud device are pulled from the user's Plaud cloud library (Plaud CLI, OAuth). Transcripts come with speaker labels; a Plaud transcript export can also be uploaded. |
| **Crusoe** | Understanding. Every note (voice, uploaded or typed) is read by `openai/gpt-oss-120b` on Crusoe Managed Inference, with JSON-schema output (~1–2 s). Kimi K2.6 on Crusoe is the vision model for labour-plan photos. Open-weight models keep competitors' schedules away from closed-model vendors. The app is designed to be hosted on a Crusoe VM. |
| **Neo4j** | The backbone. Every site, step, dependency, crew, booking and subcontractor approval is a graph in Neo4j Aura. Cypher traces the ripple from a delayed step to handover, and finds swap partners: the same subcontractor, approved at both companies, booked within 10 km (`point.distance`). A live "Graph activity" panel shows each query. |

## Architecture

```
Plaud cloud ──► ingest ──► Crusoe (gpt-oss-120b) ──► proposed change ──► site confirms ──► PM approves
                                                                                              │
                          Neo4j Aura (dependency + network graph) ◄── event log ◄─────────────┘
                                   │
            labour balance (surplus / shortage / clash) ──► sync engine (mechanisms, lead time)
                                   │
            Sync Board ──► offer / request / link / pool ──► each company confirms its own booking
```

- **Backend:** Python 3.11, FastAPI, pydantic; an in-memory engine mirrored to Neo4j (parity-tested).
- **Frontend:** a single `static/index.html` (vanilla JS + SVG), with a role switcher (Dan, Priya, Marcus, Sam).
- **Visibility:** each company sees its own projects in full, and others only as anonymised offers and requests, enforced server-side and tested.
- **Tests:** 53 offline tests plus live Neo4j parity tests (`uv run pytest`).

## Run it

```bash
uv sync
cp .env.example .env        # add CRUSOE_API_KEY, NEO4J_URI/USER/PASSWORD, STORE=neo4j
plaud login                 # optional: connect your Plaud cloud library
uv run uvicorn app.main:app --port 8000
# open http://localhost:8000, click "Reset demo", press G for the guided script
```

Without keys it still runs: in-memory graph, and an offline extractor instead of Crusoe.

## Docs

- `docs/00-business-model.md`: business model and reasoning
- `docs/01-product-requirements.md`: PRD (v2.1)
- `docs/02-technical-spec.md`: technical spec (v2.1)
- `docs/04-labour-mobility-research.md`: short-notice labour research (UK, NYC, Paris, Dubai, Hong Kong)
- `docs/demo-scripts.md`: Plaud recording scripts and video structure
- `docs/neo4j-demo.md`: Cypher queries for the Neo4j console
