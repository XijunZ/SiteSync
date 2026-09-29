# SiteSync: Product Requirements (PRD)

| | |
|---|---|
| Status | Draft for review |
| Date | 2026-09-29 |
| Context | The AI Conference Hack Day, Pier 48 SF. Build 9:00 to 19:00, demo at the end. |
| Source brief | `CLAUDE.md` (identical `AGENTS.md` for Codex) |
| Next doc | `02-technical-spec.md` |

## 1. Problem

On a residential development, every site runs to a programme of about 50 dependent on-site steps. When something slips (rain on the roof, a late inspection), the programme is updated by hand, days later, in a spreadsheet. Three things go wrong:

1. **Nobody sees the knock-on effect.** A 5-day roof delay quietly pushes services, drylining, fit-out and handover. Contractors find out when crews turn up to a site that is not ready.
2. **Crews sit idle and still get paid.** A crew booked for a step that has slipped has nothing to do for those days. At roughly £1,200 per crew-day this is pure waste.
3. **Idle capacity is invisible to the market.** A different contractor two miles away may need exactly that trade in exactly that window, but contractors do not share schedules because they are competitors.

The signals that a delay has happened already exist. They are just unstructured: a voice note from a site manager, a photo of a whiteboard labour plan, a weather forecast.

## 2. Product vision

> SiteSync turns messy site updates into a live, predicted programme, spots crews that a delay will leave idle, and quietly offers that capacity to nearby sites without either contractor seeing the other's business.

## 3. Goals and non-goals

### Goals (for hack day)

- G1. Show that one unstructured input (a voice-note transcript) can update a structured programme correctly, with a human confirming the change.
- G2. Show the delay propagating through a real dependency graph and changing the predicted finish date.
- G3. Show a newly idle crew being detected and matched to another contractor's nearby site.
- G4. Prove neutrality: each contractor sees only its own data, even inside LLM prompts.
- G5. Use sponsor tools meaningfully (Neo4j, OpenRouter, Plaud) for prize eligibility.

### Non-goals

- Real calendars, bank holidays, or partial working days (we use integer working days).
- Authentication, user accounts, permissions beyond the GC switcher.
- Real crew availability, contracts, payments, or booking confirmation between GCs.
- Resource levelling or schedule optimisation (we predict and alert; humans decide).
- Mobile app, notifications, or integrations with Procore, Asta, MS Project, etc.
- Pre-construction phases (acquisition, design, planning). On-site phases F to L only.

## 4. Personas

### Primary

**P1. Dan, site manager (Northgate Build, Site A)**
- On site all day, hands full, sends updates as voice notes or photos. Does not open spreadsheets.
- Needs: report a problem in 20 seconds and trust that the right people find out.
- Pain: the programme is always out of date; gets blamed for knock-on delays he flagged weeks ago.
- Success: says "roofing delayed, heavy rain, about five days" and sees the programme update correctly after one tap to confirm.

**P2. Priya, operations director (Northgate Build, runs Sites A and B)**
- Office-based, owns the programme and crew bookings across her sites. Answerable for cost and finish date.
- Needs: see which steps and crews a delay actually affects, and what it costs, without reading 50 lines.
- Pain: idle crews discovered after the fact; no way to recover the cost.
- Success: an alert tells her the M&E crew is idle for 5 days, and that a vetted opportunity exists nearby worth about £6,000.

**P3. Marcus, operations director (Riverside Construction, runs Sites C and D)**
- Same role as Priya at a competing GC. Would never share his programme with Northgate.
- Needs: extra trade capacity at short notice, especially M&E, which is scarce.
- Success: sees "a vetted M&E crew is available days X to Y" with no mention of who or why, and never sees Northgate's sites.

### Secondary

**P4. Independent subcontractor (M&E or drylining firm working for both GCs)**
- Wants continuous work and hates being double-booked by two clients. In the MVP they are represented only as data (a shared crew that can clash). There is no subcontractor UI.

**P5. Hack day judge (demo audience)**
- Has 3 to 5 minutes. Needs to understand the problem, see a real AI step, see the graph do something non-trivial, and see sponsor tools used. Will be put off by a crash or a long loading spinner.

## 5. User stories and acceptance criteria

Priority uses MoSCoW. **Must = MVP.**

### Must (MVP)

| ID | Story | Acceptance criteria |
|---|---|---|
| US-1 | As Priya or Marcus, I can switch between GCs and see only my own sites. | Switching GC changes the site list, timelines and alerts. No other GC's site names, IDs or step details appear anywhere in the UI or API response for that GC. |
| US-2 | As Priya, I can see each site's timeline with planned vs predicted bars. | Each step shows a grey planned bar and a coloured predicted bar. Steps that moved are visibly different. Weather-sensitive steps are marked. A "today" line is shown. |
| US-3 | As Dan, I can paste or upload a voice-note transcript and get a proposed schedule update. | Given "roofing delayed, heavy rain, about five days" for Site A, the system proposes `{site: A, step: J1, delay_days: 5, reason: weather}` within 10 s. If the step is ambiguous, it returns candidates instead of guessing. |
| US-4 | As Dan or Priya, I confirm a proposed update before it changes anything. | Nothing is written until Apply is clicked. The proposal can be edited or dismissed. |
| US-5 | As Priya, applying a delay updates every downstream step's predicted dates. | After a 5-day delay on A-J1, the 18 downstream steps on Site A shift by 5 days and the predicted finish moves by 5 days. Other sites are unchanged. |
| US-6 | As Priya, I am alerted to crews newly left idle by the delay. | Exactly one alert for the demo: the Northgate M&E crew is idle for 5 working days (days 230 to 235) before A-K3. Gaps that already existed in the plan are not alerted. |
| US-7 | As Priya, I see a cross-GC opportunity for my idle crew, without the other GC's details. | Alert shows "a nearby site needs M&E for 5 days in this window, about 2 km away" with days and £ value (5 × £1,200 = £6,000). No GC name, site name or step name from Riverside. |
| US-8 | As Marcus, I see the same opportunity from my side, anonymised. | Riverside sees "a vetted M&E crew is available days 230 to 235" linked to Site C first fix. No Northgate details. |
| US-9 | As the demo presenter, I can reset to the planned programme. | One click restores all predicted dates to planned and clears alerts, so the demo can be rerun. |
| US-10 | As a judge, I can see what the AI did and what it cost. | Footer shows number of LLM calls, models used, and total cost in USD. |

### Should

| ID | Story | Acceptance criteria |
|---|---|---|
| US-11 | As Dan, I can upload a photo of a handwritten labour plan and get proposed crew bookings. | Vision model returns rows `{site, trade, crew_name, start_day, end_day}` with a confidence score, shown for confirmation before writing. |
| US-12 | As Priya, I am alerted when a shared subcontractor crew is double-booked across sites. | Clash alert shows the crew and overlapping days, with the other site anonymised if it belongs to another GC. |
| US-13 | As Priya, alerts are written in plain English. | A stronger LLM writes one short alert per GC, using only that GC's data plus anonymised offers. |
| US-14 | As Dan, voice notes arrive directly from Plaud. | If Plaud provides API or export access, transcripts are pulled in. Otherwise, text upload is used (same pipeline). |

### Could

| ID | Story |
|---|---|
| US-15 | Weather risk flag on weather-sensitive steps in the next 2 weeks (Open-Meteo, or Brave Search). |
| US-16 | Deployed at a public URL (Vultr or Crusoe). |
| US-17 | Critical path highlighted on the timeline. |

### Won't (this build)

Auth, real dates or calendars, booking confirmation between GCs, subcontractor-facing UI, notifications, pre-construction phases.

## 6. MVP definition

**The MVP is the demo story, end to end, reliably:** US-1 to US-10.

In plain terms, a judge watches this happen in under 3 minutes:

1. Northgate view: its two sites (A and B), timelines on plan.
2. Paste Dan's transcript. The system proposes "Site A, roof waterproofing (J1), +5 days, weather". Presenter clicks Apply.
3. Site A's timeline visibly shifts. Predicted handover moves 5 days.
4. Alert: "M&E crew idle 5 days (days 230 to 235). A nearby site needs M&E then. Potential saving £6,000."
5. Switch to Riverside. Different sites, no Northgate data. Alert: "A vetted M&E crew is available days 230 to 235 for your Site C first fix."
6. Footer: 1 to 2 LLM calls, models, cost under $0.01.
7. Reset.

Photo ingestion (US-11) is the first thing added after the MVP works.

## 7. Success metrics (for the demo)

| Metric | Target |
|---|---|
| Demo story runs end to end from a clean seed | 3 times in a row with no manual fixes |
| Transcript to proposal latency | under 10 s |
| Apply to updated timeline and alerts | under 2 s |
| Neutrality leaks (other GC's names or site details in UI, API or prompts for a GC) | 0 |
| Engine tests | all green |

## 8. Assumptions and constraints

- One working day is the unit of time. "Today" is a fixed global day (day 220) for reproducibility.
- The reference programme is the same for all four sites; sites differ only by start offset.
- Crew-day cost is £1,200, stated on screen as an assumption.
- One crew per trade per GC, plus two independent crews (M&E, drylining) shared by both GCs.
- Tools: Neo4j Aura Free, OpenRouter (OpenAI SDK), Python 3.11, FastAPI, vanilla JS. If Neo4j is unavailable, an in-memory networkx store with the same interface is used.

## 9. Risks and decisions needed

Found by simulating the seed programme (see spec section 4 for numbers).

| # | Finding | Proposed decision |
|---|---|---|
| R1 | In the CSV as given, a 5-day delay to J1 (roofing) changes nothing downstream except the J6 milestone, because drylining K8 has 13 days of slack. The demo story would fall flat. | Add one dependency: **K3 (M&E first fix) depends on J6 (building weathertight)**. Realistic, since services go in once the building is dry. The delay then shifts 18 steps. |
| R2 | Planned M&E work already has gaps of 14 to 33 days, so "any gap over 2 days" would produce noisy alerts and break "exactly one gap". | Alert only on idle time **created by a delay** (planned start to predicted start, minus other bookings), within a **20 working-day lookahead** from today. |
| R3 | `owner_or_trade` mixes trades, combined trades ("Groundworks, concrete") and non-crew owners (Council, Building control, Milestone). | Normalise with a fixed mapping table. Non-crew owners get no crew. |
| R4 | Site C cannot be "just before first fix" and have first fix start exactly inside a 5-day gap. | Match on **overlap of at least 3 days** between the gap and the other site's step window, not only "start inside gap". |
| R5 | Neo4j prize might not exist, or Aura setup may be slow. | Build against the store interface. networkx first if needed, Neo4j swapped in behind it. |
| R6 | LLM variability breaks the live demo. | Structured output with pydantic, a fixed demo transcript, and a cached fallback response if OpenRouter fails. |

## 10. Open questions

1. Is the Neo4j prize confirmed? (Affects how much time goes into Cypher vs networkx.)
2. Do we have Plaud API or export access, or is it transcript upload only?
3. Which GitHub account and repo name for submission?
4. Are decisions R1 to R4 accepted? They change the brief in `CLAUDE.md`, which Codex also reads.
