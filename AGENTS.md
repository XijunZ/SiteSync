# Project brief: SiteSync (working name)

Hack day build, The AI Conference Hack Day, Pier 48 SF. Code must be written today and submitted as a GitHub repo. Build window 9am to 7pm; demo at the end. Favour a working, reliable demo over breadth.

## What we are building

A construction timeline engine for property developers and general contractors (GCs).

1. Hold each site's programme as a dependency graph of steps.
2. Take messy real-world signals (a photo of a labour plan, a voice note transcript, a weather forecast) and turn them into schedule updates using an LLM.
3. Propagate any delay through the dependency graph to predict the real finish date of every downstream step.
4. Detect crews that become idle or double-booked because of the shift.
5. Match idle crews to other GCs' nearby sites that need the same trade in the same window.

Neutrality rule: each GC only ever sees its own sites and its own alerts. Cross-GC matches are shown as "a vetted crew is available from date X to Y", never revealing the other GC's project details.

## Demo story (build towards exactly this)

- Two GCs (Northgate Build, Riverside Construction), four London sites at offset stages.
- A voice note arrives from Site A: "roofing delayed, heavy rain, about five days."
- The engine shifts every downstream step on Site A. The planned vs predicted timeline visibly moves.
- Site A's M&E crew now has a 5-day idle gap.
- The engine matches that crew to Riverside's Site C, which needs M&E first fix in that window.
- Each GC's screen shows only its own alert, with days and money saved.
- Second input: a photo of a handwritten labour plan is uploaded and parsed into bookings.

## Sponsor tools to use (prize eligibility)

- **Neo4j (Aura Free):** the dependency graph and all scheduling queries. Confirm the Neo4j prize exists before over-investing; if Neo4j is unavailable, fall back to an in-memory graph with `networkx` behind the same interface.
- **OpenRouter:** all LLM calls, through the OpenAI SDK with `base_url="https://openrouter.ai/api/v1"`. Use a cheap fast model for extraction, a stronger model for delay reasoning and alert wording, and a fallback model list. Log model, tokens and cost per call and show cost in the UI.
- **Plaud:** voice notes from site managers. Use Plaud's export or API if the sponsor provides access; otherwise accept an uploaded transcript text file with the same pipeline.
- **Brave Search API:** optional, for weather-driven delay risk on weather-sensitive steps. If it proves flaky, use Open-Meteo (free, no key) and keep Brave for looking up public site info.
- **Vultr or Crusoe:** deploy the app once it works locally. Deployment is last priority.

## Tech stack

- Python 3.11, FastAPI, `neo4j` driver, `openai` SDK (pointed at OpenRouter), `pydantic` for schemas.
- Frontend: a single `static/index.html` with vanilla JS and SVG for the timeline. No build step.
- Config via `.env`: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `OPENROUTER_API_KEY`, `BRAVE_API_KEY`.
- Never commit `.env`. Add `.env.example`.

## Repo layout

```
app/
  main.py            FastAPI app and routes
  graph.py           Neo4j queries (propagation, idle detection, matching)
  llm.py             OpenRouter client, model routing, cost logging
  ingest.py          photo and transcript extraction to structured updates
  weather.py         forecast lookup for weather-sensitive steps
  schemas.py         pydantic models shared by all modules
seed/
  development_programme_seed.csv   75-step reference programme
  seed.py            builds GCs, sites, steps, crews in Neo4j
static/index.html    UI
tests/               engine tests on the seed data
README.md            setup, demo script, sponsor usage
```

## Data model (Neo4j)

```
(:GC {id, name})-[:RUNS]->(:Site {id, name, lat, lon, start_date})
(:Site)-[:HAS_STEP]->(:Step {id, code, name, trade, days, kind, weather_sensitive,
                             planned_start, planned_end, pred_start, pred_end, risk})
(:Step)-[:DEPENDS_ON]->(:Step)          finish-to-start only
(:Step)-[:ASSIGNED_TO]->(:Crew {id, name, trade})
(:GC)-[:EMPLOYS]->(:Crew)               some crews are independent subcontractors shared by both GCs
```

- `kind` is one of `task`, `approval`, `wait`, `milestone`. Approval and wait steps have no crew.
- Dates are working days as integers from a common day zero (simpler than calendars for the demo). Convert to real dates only in the UI.

## Seed data

- Source: `seed/development_programme_seed.csv` (columns: id, phase, riba_stage, name, owner_or_trade, duration_working_days, depends_on separated by `;`, weather_sensitive, kind, delay_risk).
- For the demo, only load the on-site phases: IDs starting F, G, H, J, K, L. Drop dependencies that point to earlier phases.
- Create four sites, each a copy of that programme with step IDs prefixed by site (e.g. `A-K3`). Offset start dates so the sites are at different stages on "today": Site A at the roof (J1), Site B at ground works (G5), Site C just before first fix (K1), Site D in demolition (F7).
- Sites: A and B run by Northgate, C and D by Riverside. Use real-looking East London coordinates within about 5 km of each other.
- Crews: one crew per trade per GC, plus two independent subcontractor crews (M&E and drylining) booked by both GCs, so clashes can occur.
- Engineer the offsets so the demo delay on Site A creates exactly one clean idle gap that matches Site C. Write a test that asserts this.

## Core engine (graph.py)

1. **Apply update:** set `pred_end` (and `pred_start` if needed) on the affected step.
2. **Propagate:** run this until it returns 0, capped at 50 iterations:

```cypher
MATCH (s:Step)-[:DEPENDS_ON]->(d:Step)
WITH s, max(d.pred_end) AS ready
WHERE ready > s.pred_start
SET s.pred_start = ready, s.pred_end = ready + s.days
RETURN count(s) AS shifted
```

3. **Idle gaps:** for each crew, order its steps by `pred_start` and return gaps between consecutive steps longer than 2 days.
4. **Clashes:** same crew, overlapping predicted windows, on different sites.
5. **Matching:** for each idle gap, find steps on other sites (any GC) needing the same trade whose predicted start falls inside the gap and whose site is within 10 km (`point.distance`). Rank by overlap days, then distance.
6. **Reset:** restore all `pred_*` to `planned_*` so the demo can be rerun.

Keep every query in `graph.py`. Expose a Python interface so the networkx fallback can implement the same functions.

## LLM pipeline (llm.py, ingest.py)

- **Photo of labour plan:** vision model, structured output against a pydantic schema: list of `{site, trade, crew_name, start_day, end_day}` plus a confidence score. Show extracted rows to the user for confirmation before writing.
- **Voice note transcript:** cheap model extracts `{site, step_code or trade, delay_days, reason}`. If the step is ambiguous, return candidates rather than guessing.
- **Alert wording:** stronger model writes one short alert per affected GC from the engine output. Inputs to this call must be filtered to that GC's own data plus anonymised capacity offers, so neutrality holds even inside prompts.
- Every call goes through one function that handles model routing, fallback, retries, and logs model, latency, tokens and cost.
- Keep prompts in one file so they are easy to tweak.

## API contract (build backend and frontend against this)

```
GET  /api/sites?gc={gc_id}                  sites for one GC
GET  /api/timeline?site={site_id}           steps with planned and predicted dates, crit flag
POST /api/ingest/transcript   {text}        returns proposed update(s)
POST /api/ingest/photo        multipart     returns proposed bookings
POST /api/updates/apply       {updates[]}   applies, propagates, returns summary
GET  /api/alerts?gc={gc_id}                 idle gaps, clashes, matches for that GC only
POST /api/demo/reset                        restore planned dates
GET  /api/llm/log                           recent calls with model and cost
```

Responses are JSON with snake_case keys. Errors return `{error, detail}` with a clear message.

## UI (static/index.html)

- GC switcher at the top (Northgate, Riverside). Switching must visibly change what is shown, proving neutrality.
- Timeline per site: planned bar in grey, predicted bar overlaid in colour, critical steps highlighted, weather-sensitive steps marked.
- Input panel: paste or upload a transcript, upload a photo, see the extracted update, click Apply.
- Alerts panel: idle crew, clash, and match cards with days and estimated money saved (assume a crew day costs £1,200 for the demo and state the assumption on screen).
- Small footer showing LLM calls, models used and total cost.
- Reset button for rerunning the demo.

## Timeboxed plan

1. **By 10:30:** repo scaffold, `.env`, Neo4j Aura connected, seed script loads four sites. Propagation works on a manual delay (test passes).
2. **By 12:30:** idle gaps, clashes, matching. Engine tests pass on the seed data. API endpoints return real data.
3. **By 14:30:** transcript and photo ingestion via OpenRouter, with confirmation step.
4. **By 16:30:** UI complete, full demo runs end to end locally.
5. **By 17:30:** deploy (Vultr or Crusoe), weather lookup if time allows, README with sponsor usage.
6. **17:30 to 19:00:** rehearse demo, fix bugs only, record a backup video of the demo, push final code.

## Splitting work between Claude Code and Codex

Run them in parallel on separate branches, merging often. The API contract above is the boundary.

- **Claude Code:** `seed/`, `app/graph.py`, `app/schemas.py`, engine tests, API routes in `app/main.py`.
- **Codex:** `static/index.html`, `app/llm.py`, `app/ingest.py`, `app/weather.py`, README.
- Codex builds the UI against mocked JSON matching the contract until the real endpoints land.
- Only `schemas.py` is shared; change it in one place and tell the other agent.

## Rules for the agents

- Build the smallest thing that makes the demo story work, then harden it. No features outside the demo story unless everything above is done.
- Write tests for the engine first and keep them green.
- Commit small and often with clear messages. Never commit secrets.
- If a sponsor API fails or needs approval, stub it behind the same interface and keep moving; note it in the README.
- Prefer boring, reliable code. No new frameworks, no build tooling.
- Ask before deleting files or changing the API contract.

## Definition of done

- `python seed/seed.py` then `uvicorn app.main:app` runs the full demo from a clean database.
- The voice-note delay on Site A produces the idle gap and the Site C match, every time.
- Switching GC shows only that GC's data.
- README explains setup, the demo script, and how each sponsor tool is used.
- Code pushed to a public GitHub repo.
