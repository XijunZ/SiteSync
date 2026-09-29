# SiteSync: Technical Setup and Delivery Process

| | |
|---|---|
| Date | 2026-09-29 |
| Reads with | `01-product-requirements.md`, `02-technical-spec.md` |

## 1. Prize-driven integration requirements

From the hack day prize list. **Crusoe is mandatory**: every overall cash prize ($5k, $3k, $2k) requires it.

| Sponsor | Prize at stake | How SiteSync uses it (must be real work, not a logo) | Where |
|---|---|---|---|
| **Crusoe** | Overall 1st to 3rd (required) | (a) **Primary LLM inference**: transcript extraction (gpt-oss-120b) and delay reasoning / alert writing (Kimi K2.6) run on Crusoe Managed Inference. (b) **Hosting**: the app runs on a Crusoe Cloud VM for the demo. | `app/llm.py`, deploy |
| **Neo4j** | Best Use, Best Technical, Most Creative | The programme *is* the graph: dependency propagation, crew clash detection and geo-matching are Cypher queries on Aura (`point.distance`, variable-length dependency paths for "what does this delay touch"). | `app/graph.py` |
| **Plaud** | Best Use ($1k), Second ($500) | The site manager records a voice note on a Plaud device or app. SiteSync pulls it through the Plaud CLI (`plaud today`, `plaud transcript <id> --polished`), then extracts the delay. The UI has a "Sync from Plaud" button. | `app/plaud.py`, `POST /api/ingest/plaud` |
| **OpenRouter** | Counts toward DuploCloud "most sponsor tools" | (a) **Vision**: labour-plan photo parsing (Gemini 3.8 Flash; Crusoe has no vision model). (b) **Fallback routing**: if a Crusoe call fails, the same request goes through OpenRouter. The cost log shows which provider served each call. | `app/llm.py` |

Not pursued (out of scope unless everything else is done): BAND (needs agent coordination through a Band room), Vultr (LEGO prize; Crusoe covers hosting), DuploCloud "Best Agent".

**Demo line for judges:** "Plaud captures the voice note, Crusoe's open models turn it into a schedule change, Neo4j propagates it through the programme graph and finds an idle crew a competitor can use, and OpenRouter reads the handwritten labour plan and backs up Crusoe."

## 2. Local environment (done)

| Item | Status |
|---|---|
| Python 3.11.16 via `uv` | installed |
| Project deps (`pyproject.toml`, `uv.lock`) | installed with `uv sync` |
| `neo4j-cli` v1.14.0 and its Claude Code skill | installed |
| Plaud CLI 0.3.14 (`@plaud-ai/cli`) | installed, **not logged in** |
| GitHub CLI, logged in as XijunZ | done |
| `.env.example` | created |

Common commands:

```bash
uv sync                              # install deps
uv run pytest                        # tests (in-memory store by default)
uv run python seed/seed.py           # load 4 sites into the configured store
uv run uvicorn app.main:app --reload # run on http://localhost:8000
```

## 3. Accounts and keys (needs you, in this order)

Put every secret in `.env` (copy from `.env.example`). Do not paste secrets into chat.

| # | What | Where | Goes into | Time |
|---|---|---|---|---|
| 1 | **Crusoe Intelligence API key** | console.crusoecloud.com → Admin → Security → Intelligence API keys. Ask the Crusoe booth for hack day credits. | `CRUSOE_API_KEY` | 5 min |
| 2 | **Neo4j Aura Free instance** | console.neo4j.io → New instance → Free. Download the credentials file shown once at creation. | `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`; set `STORE=neo4j` | 5 min (plus about 2 min to provision) |
| 3 | **OpenRouter key** | openrouter.ai/keys. Add $5 credit. | `OPENROUTER_API_KEY` | 3 min |
| 4 | **Plaud login** | Run `plaud login` in a terminal (browser OAuth). You need a Plaud account, and ideally a Plaud device from the booth to record the demo voice note. | CLI token store (no `.env` entry) | 3 min |
| 5 | **Crusoe Cloud VM access** (for deploy) | Same Crusoe console → Compute → create an SSH key and a small CPU VM. Ask the booth which instance type the credits cover. | SSH host in `docs/deploy.md` | 10 min, do by 12:30 |
| 6 | **GitHub repo** | I can create it with `gh repo create`, public, once you pick a name. | remote `origin` | 1 min |

Ask at the booths:
- **Crusoe:** credits, and whether they judge "use" as inference, compute, or both. We plan both.
- **Plaud:** a loaner device, and whether hack day partner access to the Transcription API exists. The CLI path works without it.
- **Neo4j:** judging criteria for "Best Technical Implementation".

## 4. Process (SDLC, compressed to one day)

```
Requirements ─► Spec ─► Setup ─► Build (TDD) ─► Integrate ─► Deploy ─► Verify ─► Demo
   PRD 01       02        03      per module     merge to     Crusoe    3 clean    rehearse,
   (done)      (done)   (this)    tests first    main each    VM        runs       record backup
                                                 milestone
```

### 4.1 Gates (nothing moves forward until its gate passes)

| Gate | Pass condition | Who checks |
|---|---|---|
| G0: Design approved | You approve PRD, spec and the 7 brief changes (spec §11) | You |
| G1: Engine | `uv run pytest` green on the in-memory store; demo numbers from spec §5.8 asserted | Claude |
| G2: Neo4j parity | Same tests green with `STORE=neo4j` against Aura | Claude |
| G3: API | All routes return real data; neutrality test green; fixtures published for Codex | Claude |
| G4: AI inputs | Plaud sync gives transcript → proposal on Crusoe; photo gives bookings on OpenRouter; fallback works with the Crusoe key removed | Codex + Claude |
| G5: End to end | Full demo story runs 3 times from `seed` + reset, locally | You |
| G6: Deployed | Same on the Crusoe VM public URL | You |
| G7: Submission | Public repo, README (setup, demo script, sponsor usage), backup video | You |

### 4.2 Working rules

- **Branches:** `main` must always be demo-able. Claude works on `claude/engine`, Codex on `codex/ui-llm`. Merge to `main` at each gate.
- **Contract first:** `app/schemas.py` and the API in spec §7 are the boundary. Change either only after telling the other agent and updating the spec.
- **Tests first** for engine logic. Codex's LLM tests mock `llm.call`.
- **Commits** are small and frequent, with no secrets. `.env` is git-ignored.
- **Stubs over blockers:** if a sponsor API stalls, put a stub behind the same interface, note it in the README, and keep moving.
- **Code freeze at 17:30.** After that, bug fixes only.

### 4.3 Timeline (revised for the 10:30 start)

| By | Gate | Claude Code | Codex | You |
|---|---|---|---|---|
| 10:45 | G0 | | | Approve design; start keys 1 to 4 |
| 11:45 | G1 | schemas, seed, in-memory store, engine, tests green | UI skeleton against fixtures; `llm.py` with Crusoe + OpenRouter | Keys in `.env`; Plaud device; record demo voice note |
| 12:30 | G2, G3 | Neo4jStore + parity; routes; views; neutrality test | Timeline SVG, GC switcher | Crusoe VM (key 5); **smoke-deploy hello world** |
| 14:30 | G4 | `/api/ingest/plaud`, apply flow, hardening | Transcript + photo ingest, confirm flow | Test on real Plaud recordings |
| 16:30 | G5 | Bug fixes; deploy script | Alerts panel, LLM cost footer, polish | Run demo 3× |
| 17:30 | G6 | Deploy to Crusoe | README | Verify public URL |
| 19:00 | G7 | Fixes only | Fixes only | Rehearse, record backup video, submit |

Deployment moved from "last" to a smoke deploy at 12:30, because Crusoe is a qualifying requirement and VM setup is the step most likely to surprise us.

## 5. Risks

| Risk | Mitigation |
|---|---|
| No Crusoe credits or key delay | Ask the booth first thing. Worst case: $5 free credits cover hundreds of small calls. |
| Crusoe models don't support JSON schema output | Use JSON mode plus pydantic validation and one retry; OpenRouter fallback |
| Plaud login or device unavailable | Upload the transcript text (same pipeline); say so honestly in the demo |
| Aura Free provisioning slow or down | In-memory store (same interface); rerun parity tests when Aura is back |
| Live LLM flakiness during judging | Canned response for the exact demo transcript, flagged `fallback` in the log |
| Venue Wi-Fi | Phone hotspot; backup video |
