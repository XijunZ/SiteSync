# Demo Video Plan (6 min)

Structure from the organisers: problem, tech stack, live demo + code.

## Before recording
1. localhost:8000 → Reset demo → hard refresh (⌘⇧R); browser zoom ~90%.
2. `docs/slides.html` open (F = full screen, ← → to switch).
3. Plaud video ready to play.
4. GitHub code tabs: `app/plaud.py#L71-L92`, `app/ingest.py#L39-L50`, `app/llm.py#L9-L16`, `app/graph_neo4j.py#L14-L29`, `app/sync_engine.py#L76-L83` (zoom 125–150%).
5. Optional: Neo4j Aura console with the query in `docs/neo4j-demo.md`.

## 1. Problem (0:00–1:00)
- **Slide 1 (~35 s):** construction sites don't fail alone; common causes (material failures, weather, inspections, no-shows, design changes, equipment); effects (idle crews, shortages nearby, late handovers, found out too late).
- **Slide 2 (~25 s):** today = calls and spreadsheets; SiteSync process: capture → understand → propagate → flag gaps → next best action → match & agree → prove. Customer: the GC (per-project fee + share of days protected).

## 2. Tech stack (1:00–2:00)
- **Slide 3:** Plaud (capture), Crusoe (gpt-oss-120b extraction ~1 s; Kimi K2.6 vision; open-weight, hosted on Crusoe, so competitors' data stays private), Neo4j (delay = path, fix = cross-company pattern via Cypher + point.distance).

## 3a. Live demo (2:00–5:00)
| Time | Who | Action |
|---|---|---|
| 2:00 | — | Play Plaud video |
| 2:10 | Dan | Sync from Plaud → "Site Update: Hackney Wick Yard" → transcript |
| 2:25 | Dan | Propose → Crusoe panel (J1 +5d, ~1 s) |
| 2:40 | Dan | Knock-on: 18 steps, 397 → 402, NEW Sparks crew 1 idle 230–235; Neo4j ripple |
| 2:55 | Dan | Confirm fact |
| 3:00 | Priya | Approvals → Approve |
| 3:10 | Priya | Sync Board: no action 405 vs 402 → 3 days, £24,000; "How we found this · Neo4j" |
| 3:30 | Priya | Offer to nearby projects |
| 3:40 | Marcus | Sync Board → short 6 M&E → Request capacity |
| 3:55 | Marcus | Request matched → Overlay → Request this crew |
| 4:15 | Priya | Requests → Accept + terms (back by day 235) |
| 4:30 | Sam → Marcus → Priya | Accept → Confirm → Confirm |
| 4:45 | Priya | Days protected report: 3 days, £24,000; Sparks £6,000 idle avoided |

## 3b. Code (5:00–5:50)
plaud.py (Plaud cloud) → ingest.py + llm.py (Crusoe, strict JSON) → graph_neo4j.py (ripple + swap Cypher; linger) → sync_engine.py (days protected).

## Close (5:50–6:00)
"Plaud captures, Crusoe understands, Neo4j keeps every site in sync. That's SiteSync."

**Long?** Skip "How we found this" and sync_engine.py. **Short?** Add 15 s of the Neo4j Aura graph.
