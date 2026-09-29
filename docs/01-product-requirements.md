# SiteSync: Product Requirements (PRD v2)

| | |
|---|---|
| Status | Draft v2 for review. Replaces v1 (written before the business model changed). |
| Date | 2026-09-29 |
| Based on | `00-business-model.md` (CURRENT MODEL v5), `04-labour-mobility-research.md`, and the design brainstorm of 2026-09-29 |
| Next | `02-technical-spec.md` v2 |

## 1. Identity

**SiteSync keeps construction sites in sync.** It is the next-best-action engine that finds what falls out of sync when a timeline moves (crews, equipment, inspections, bookings, across sites and companies) and puts the right mechanism in front of the PM early enough for it to work.

- **Not an ERP.** We are not the system of record for the project. We read from the tools and habits sites already use.
- **Not a prediction tool.** The forecast is an input. The product is the **action**.

## 2. Problem

Construction sites don't fail alone. When one site slips, the crews, equipment, inspections and deliveries booked against the old plan, on that site, on the company's other sites, and on other companies' sites, fall out of sync. Today:
- The knock-on effect is found late (at the morning briefing, or when a crew turns up to an area that isn't ready).
- Labour surplus and shortage are discovered on the day, when only expensive fixes remain (agency labour at short notice, idle paid crews, overtime).
- Companies can't see each other's needs, so a surplus on one site and a shortage 2 km away never meet.
- Subs hedge by overbooking, which causes no-shows. GCs hedge by padding programmes, which delays completion.

Each extra week of warning unlocks more ways to fix a mismatch (see §6.4). **SiteSync's job is to turn timeline changes into early, specific, executable actions.**

## 3. Customer and users

**Customer (signs and pays):** the general contractor (GC). Pricing is deferred (see business model); candidate structure: base fee per project as a preliminaries line + fill margin + optional turn-up guarantee.

| Persona | Role in real life | Role in SiteSync |
|---|---|---|
| **Dan, site manager** (Northgate, Site A) | Runs the site day to day: trades, sequencing, safety, deliveries, site diary | **Source of truth for the site.** Reports progress, blockers, readiness and headcount at any time; confirms facts |
| **Priya, PM** (Northgate, Sites A and B) | Owns programme, cost, subcontract packages, client contract | **Owner of commitments.** Confirms material date changes, decides mechanisms, re-baselines, manages links and pools |
| **Operations director** (Northgate) | Portfolio of projects | Portfolio view; escalations only |
| **Marcus, PM** (Riverside, Sites C and D) | Same as Priya at a different GC | Sees Northgate's projects only in anonymised form; accepts or declines link requests and proposals |
| **Sparks planner** (M&E subcontractor working for both GCs) | Schedules crews across clients | Sees only its own bookings; accepts or declines proposals involving its crews |
| **SiteSync operator** (internal) | — | Runs cross-company proposals where no link exists yet (stage 1) |

## 4. Core concepts

1. **Backbone: timeline built on a dependency graph.** Per project: steps, finish-to-start dependencies, durations, **labour loading** (planned headcount per step by trade), bookings (sub, crew size, window), equipment, and the network (GCs, subs, agencies, approvals, links).
2. **Three timelines.** **Baseline** (contract programme, locked; changed only by a PM re-baseline) · **Confirmed forecast** (last approved view of reality) · **Proposed** (pending changes). Diff = proposed vs confirmed. Variance = confirmed vs baseline.
3. **Facts vs signals.** Only confirmed human facts move the **confirmed forecast**. External signals (weather, strikes, city incidents, supplier notices) move the **risk-adjusted forecast** and ask the right person to confirm the impact.
4. **Event-driven and live.** Any trigger (a human input at any time, an external signal, the clock, a counterparty reply) runs the pipeline immediately. Every change is an event with its source; state is built from events; forecasts are snapshotted per version.
5. **Labour balance.** On every change: dates → demand per trade per day → minus supply (bookings) → **surplus, shortage, clash**, and the **diff** of what this change created or resolved.
6. **Site-sync mechanisms.** A catalogue of playbooks (§6.4), each with preconditions, setup lead time, parties, steps, cost and outcome tracking.
7. **Three tiers of visibility.** **Own company:** full timelines across all own projects. **Linked partners:** only the shared pool. **City network:** anonymised timelines of other projects.
8. **Link and pool.** A company can request to link with an (anonymised) project's company. On acceptance, they agree pool terms, and pooled resources become available to cross-company mechanisms with less friction. Each completed sync leaves approved relationships (compounding moat).

## 5. User journeys

**J1: Update and see the knock-on effect (Dan, any time of day).** Dan records a Plaud note: "roofing delayed, heavy rain, about five days." SiteSync proposes *J1 finish 230 → 235*, shows the source phrase, the date knock-on (18 steps +5, handover day 397 → 402) and the **labour impact** (M&E surplus on Site A, days 230–235). Dan confirms the fact; because the finish date moves, Priya is asked to approve.

**J2: Act on what fell out of sync (Priya).** The Sync Board shows the new M&E surplus with ranked options and start-by deadlines: re-slot downstream trades (M3); slot swap with a nearby project that needs M&E in that window (M8); resequence (M1) if ready work exists. It shows the "no action" outcome (crew likely returns late: handover +8 instead of +5) vs "with action" (+5), so **3 days protected**.

**J3: Find a partner and pool (Priya → Marcus).** The matching need is on an anonymised project in the city view (~2 km, needs M&E in that window). Priya requests to link, "pool M&E capacity". Marcus sees Northgate's identity and purpose, accepts, and they agree pool terms. The slot swap proceeds; the Sparks planner accepts; each GC confirms the booking change in its own review.

**J4: A signal arrives mid-day.** A weather update (or a city incident near a site) raises risk on exposed steps. The risk-adjusted forecast shifts; Dan is asked "confirm impact?". His answer becomes a fact, and J1 continues from there.

**J5: Prove it.** A monthly report shows days protected (locked no-action snapshot vs outcome) × the GC's own day value, with the evidence trail.

## 6. Requirements

Priority: **M** = must for today's demo, **S** = should (if time), **L** = later stages.

### 6.1 Backbone and onboarding

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| B-1 | Load projects as dependency graphs with labour loading | 4 sites × 52 on-site steps; dependencies incl. K3 → J6; planned headcount per step by trade (defaults per trade) | M |
| B-2 | Network data: GCs, subs, crews, bookings, locations | Two GCs (Northgate: A, B; Riverside: C, D); Sparks (M&E) booked at A and C; East London coordinates | M |
| B-3 | Baseline locked; confirmed forecast; proposed changes | Baseline changes only via PM re-baseline (logged) | M (re-baseline: S) |
| B-4 | Import programme from MS Project / P6 / Excel / PDF | Parsed steps and dependencies, mapped and reviewed by the PM | L |

### 6.2 Capture and ingestion

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| C-1 | Voice note from Plaud → proposed changes | Demo transcript gives *Site A, J1, +5 days, weather*, with the source phrase shown. Pasted text works as a fallback. | M |
| C-2 | Typed input (field edit or free text) through the same pipeline | Same proposal, checks and diff as voice | M |
| C-3 | Entity matching with site vocabulary | "the roof" → J1; corrections saved to vocabulary | M (basic) / S (learning) |
| C-4 | Excel labour plan upload → bookings | Row-level diff vs last upload; duplicates ignored | S |
| C-5 | Photo of whiteboard labour plan → bookings (vision) | Rows with confidence, reviewed before use | S |
| C-6 | PDF reports/programmes | Text and tables extracted to fields | L |
| C-7 | Question list + ask-back: what we need to know, chase what's missing or stale | Critical steps unreported for N days surface as questions; unanswered critical questions follow up | S |

### 6.3 Change, diff and labour balance

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| D-1 | Proposed change shows date knock-on before confirming | J1 +5 → 18 steps +5, handover 397 → 402 | M |
| D-2 | Proposed change shows labour impact before confirming | New M&E surplus at Site A, days 230–235, with crew size; created vs resolved listed | M |
| D-3 | Validation | A finish before its predecessor's finish is blocked with an explanation | M |
| D-4 | Confirmation rules (option B) | Site manager confirms facts; PM also approves when the finish date or the critical path moves beyond a threshold | M |
| D-5 | Live updates and concurrency | Updates at any time; an edit against an outdated version must be re-confirmed with a refreshed knock-on | S |
| D-6 | Event log, versions, snapshots | Every change stored with source, user and time; forecast version per confirmation | M (simple) |
| D-7 | Labour balance view per trade over time (site / portfolio) | Surplus and shortage per trade per day | M (site) / S (portfolio) |

### 6.4 Sync engine and mechanisms

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| E-1 | Detect out-of-sync gaps from the labour balance diff: surplus, shortage, clash | The demo change creates the M&E surplus at A, days 230–235 | M |
| E-2 | Candidate mechanisms per gap, filtered by feasibility (setup lead time ≤ warning time, preconditions, market rules) | Options that need more warning than available are shown as unavailable, with the reason | M |
| E-3 | Rank options, each with start-by deadline, cost and days protected | "No action" vs "with action" from real propagation: handover +8 vs +5 = 3 days protected | M |
| E-4 | Mechanisms for the demo | **M1 resequence, M3 re-slot trades, M8 slot swap, M10 agency top-up** | M |
| E-5 | Other mechanisms | M4 internal redeploy, M5 equipment transfer (S); M2, M6, M7, M9, M11, M12 (L) | S / L |
| E-6 | Mechanism lifecycle | proposed → approved → in progress → confirmed → done / failed / expired; expired when the start-by deadline passes | M (simple) |
| E-7 | Combined actions | E.g. M3 + M8 together | S |

Mechanism catalogue (from the business model):

| Scope | Mechanism | Setup lead time |
|---|---|---|
| Within site | M1 Resequence · M2 Mitigate (cover, extended hours) · M3 Re-slot trades | Hours to days |
| Across own sites | M4 Internal crew redeploy · M5 Equipment / temporary works transfer · M6 Shared specialist schedule · M7 Batched inspections | Hours to weeks |
| Across companies | M8 Slot swap (shared sub) · M9 Sub-tier under approved sub · M10 Agency top-up via GC's framework · M11 Early prequalification (4+ weeks) · M12 Local-market routes | Hours to 4+ weeks |

### 6.5 Visibility, link and pool

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| V-1 | Own company sees full timelines of all its projects | Priya sees A and B in full; nothing of C or D | M |
| V-2 | City view: anonymised timelines of other projects | Area (~1 km), weeks, phase level, trade need/surplus windows; no names; confidential projects hidden | M (simple) |
| V-3 | Minimum-crowd rule for anonymisation | Only show where ≥ 3 projects in area and phase | L (demo has 4 sites) |
| V-4 | Request to link | Requester's identity revealed to target; target anonymous until it answers; accept / decline | M |
| V-5 | Pool terms | Shared resources (trades, equipment), recharge, return guarantee, priority rule, notice | M (simple form) |
| V-6 | Cross-company mechanisms require a link or an operator-run anonymised proposal | M8 between Northgate and Riverside becomes available after linking | M |
| V-7 | Subcontractor view | Sparks planner sees only its own bookings; accepts or declines proposals | M |
| V-8 | Each company's data changes only through its own confirmation | Booking changes from a slot swap are confirmed by each GC separately | M |

### 6.6 Signals

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| S-1 | Weather signal → risk flag on weather-sensitive steps → "confirm impact?" | Rain forecast over J1 raises risk; risk-adjusted forecast shifts; confirmed forecast doesn't | M |
| S-2 | City incident / strike / supplier news → scoped risk flags | Location or trade scoped; expires if marked "no impact" | S |
| S-3 | Company risk check on a proposed counterparty (news, insolvency) | One-line risk note on the option card, with sources | S |
| S-4 | Material-change notifications only (no alert spam) | Notify on threshold crossings, new gaps, deadlines within 24h | S |

### 6.7 Roles, proof, and platform

| ID | Requirement | Acceptance criteria | P |
|---|---|---|---|
| R-1 | Role/user switcher for the demo: Dan, Priya, Marcus, Sparks planner | Each view shows only what that role may see | M |
| R-2 | Permissions per §3 (site manager / PM / ops director / sub planner / operator) | Enforced server-side | M (simple) |
| R-3 | Days protected report | Locked no-action snapshot vs outcome × day value | S (single number in demo: M) |
| R-4 | AI cost and provider log | Calls, models, cost | S |
| R-5 | Authentication, real accounts | — | L |

## 7. MVP for today (the demo story)

Build exactly what makes this story work, end to end, reliably:

1. **Priya's view:** Northgate's two sites on the timeline (baseline vs forecast bars). City view shows two anonymised projects.
2. **Dan's view:** the Plaud note (or pasted transcript) → proposed change *J1 +5* with source phrase → diff: 18 steps +5, handover 397 → 402, **M&E surplus at Site A days 230–235**. Dan confirms; Priya approves (finish date moved).
3. **Weather signal:** rain over J1 shows as a risk flag (can be shown before step 2, prompting Dan's note).
4. **Sync Board (Priya):** the M&E surplus with options: M3 re-slot (always), M1 resequence (if available), **M8 slot swap** "needs a link with a nearby project that needs M&E days 225–245", M10 agency top-up for the reverse case. No action: handover +8; with action: +5, **3 days protected**.
5. **Link and pool:** Priya requests to link with the anonymised project; switch to **Marcus**, who accepts and sets simple pool terms (M&E, return by day 235).
6. **Execute:** switch to **Sparks planner**, who accepts; each PM confirms the booking change in their own review. Sync Board shows the sync done; days protected recorded.

Anything not needed for this story is out of scope today.

## 8. Non-goals (all stages unless stated)

- Being the project's system of record (ERP), document management, cost control
- Employing or supplying labour ourselves (stage 1); payments; contracts between companies (parties agree terms themselves)
- Full programme import from P6 / MS Project (later), real calendars and holidays (integer working days for now)
- Authentication and real messaging channels (WhatsApp, SMS) today

## 9. Success metrics

| Metric | Target |
|---|---|
| Demo story runs end to end from a clean seed | 3 times in a row |
| Voice note → proposed change | under 15 s (excluding Plaud's own sync) |
| Confirm → updated timeline, labour balance and options | under 2 s |
| Cross-company leakage in any view or API response | 0 |
| Engine tests (propagation, labour balance, options, visibility) | all green |

## 10. Assumptions and risks

| Item | Note / mitigation |
|---|---|
| Plaud does not auto-transcribe notes under ~5 minutes; the phone app records only with a Plaud device connected | Tap "Generate" in the app, or fetch the audio and transcribe ourselves; pasted transcript as demo fallback |
| Crusoe's docs don't confirm JSON-schema output or tool calling | Validate with pydantic, retry, fall back to JSON mode |
| Anonymised views can still leak pipeline information | Coarse area/time/phase, minimum crowd, opt-in; state it in the pitch |
| Labour loading (headcount per step) is often missing from programmes | Defaults per trade; labour plan upload overrides |
| Scope for today is large | §7 is the cut; everything else is S/L |

## 11. Open questions

1. Is the Neo4j prize the main sponsor priority after Crusoe, or Plaud? (Affects where polish goes.)
2. Demo city: keep London (East London sites), or switch to San Francisco for a local audience?
3. GitHub repo name for submission.
