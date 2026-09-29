# SiteSync: Product Requirements (PRD v2)

| | |
|---|---|
| Status | Draft v2.1. v2.1 changes the cross-company flow so the company that **needs** crew asks for it, makes the timeline the capture surface, and makes every hand-off visible (see §12). |
| Design | Clickable prototype of every MVP screen: https://claude.ai/artifact/GZZYQF4EsvVjugcq28EQfw |
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
7. **Three tiers of visibility.** **Own company:** full timelines across all own projects. **Linked partners:** only the shared pool. **City network:** anonymised projects (area, phase) and capacity **offers**; a project's week-level trade windows are visible only after its owner **shares an anonymised view** on request.
8. **Offer, request, link and pool (borrower asks).** A company with idle capacity **offers** it, anonymised (trade, crew size, days, ~1 km area). A nearby company that **needs** that trade in that window sees the offer, can request an anonymised view to check the fit, then **requests the crew**. The offering company accepts and sets pool terms (including the return guarantee), which creates the link. Each completed sync leaves approved relationships (compounding moat).
9. **The timeline is the backbone and the capture surface.** Every role lands on a timeline scoped to what it may see. Updates are made on it (click a bar, change dates, see the knock-on before proposing), or fed into it from Plaud notes, CSV and photos.
10. **Every hand-off is visible.** Each request shows who it is waiting for, then who approved it and when. Decisions stay listed after they're made, and each counterparty is notified.

## 5. User journeys

**J1: Update and see the knock-on effect (Dan, any time of day).** Dan clicks the J1 bar on his timeline and changes the finish date, or sends a Plaud note: "roofing delayed, heavy rain, about five days." Before anything is saved, the popup shows how many steps move and the new handover. SiteSync proposes *J1 finish 230 → 235*, shows the source phrase, the date knock-on (18 steps +5, handover day 397 → 402) and the **labour impact** (M&E surplus on Site A, days 230–235). Dan confirms the fact; because the finish date moves, Priya is asked to approve.

**J2: Act on what fell out of sync (Priya).** The Sync Board shows the new M&E surplus with ranked options and start-by deadlines: slot swap by **offering S1's idle days to nearby projects** (M8); re-slot downstream trades (M3); resequence (M1) if ready work exists. It shows the "no action" outcome (crew likely returns late: handover +8 instead of +5) vs "with action" (+5), so **3 days protected**. Priya offers the idle days; only trade, crew size, days and a ~1 km area are shared.

**J3: The company that needs crew asks for it (Marcus → Priya).** Marcus's timeline shows "M&E crew available near you: 6 workers, days 230–235, fits your C-K3 first fix" from anonymised project #4K1. He requests an anonymised view of #4K1; Priya sees that Riverside is asking and shares it. Marcus overlays #4K1 on his Trades view, sees the offered window line up with his need, and requests the crew. Priya accepts and sets pool terms (S1 back on Site A by day 235); only now does Marcus learn it's Northgate. The Sparks planner accepts the move; Marcus confirms his booking, then Priya confirms hers.

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
| C-0 | **Update on the timeline** | Click a bar → popup with baseline, confirmed dates and booked crews → **Update** → edit start/finish and reason → live preview ("J1 + 18 downstream steps move · handover 397 → 402 · 1 new crew gap") → Propose. Invalid edits blocked with a reason (finish before start; start before predecessors finish). An **Update timeline** menu offers the other sources (C-1, C-4, C-5). | M |
| C-1 | Voice note from Plaud → proposed changes | Demo transcript gives *Site A, J1, +5 days, weather*, with the source phrase shown. Pasted text works as a fallback. | M |
| C-2 | Typed input (field edit or free text) through the same pipeline | Same proposal, checks and diff as voice | M |
| C-3 | Entity matching with site vocabulary | "the roof" → J1; corrections saved to vocabulary | M (basic) / S (learning) |
| C-4 | CSV / Excel labour plan upload → bookings | Columns crew, step, start, end, size; each row marked new / changed / unchanged against current bookings; only new and changed rows are proposed | S |
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
| V-2 | City view: anonymised projects and open offers | Area (~1 km) and phase per project; open capacity offers; no names; confidential projects hidden. Trade windows only via V-2b | M (simple) |
| V-2b | Request an anonymised view | Requester's company is shown to the owner; owner shares or declines; once shared, the requester can overlay that project's trade windows (week level, no codes or exact dates) | M |
| V-2c | Timeline overlays | A PM can overlay another own site, or a shared anonymised view, on the Trades view of their timeline; overlapping idle/offered and needed windows are highlighted | M |
| V-2d | Offer idle capacity | From a SURPLUS gap, the PM publishes an anonymised offer (trade, crew size, days, ~1 km area). Nearby projects whose need overlaps see "crew available near you" on their timeline | M |
| V-3 | Minimum-crowd rule for anonymisation | Only show where ≥ 3 projects in area and phase | L (demo has 4 sites) |
| V-4 | Request the offered crew (creates the link) | Sent by the company that needs the crew. Requester's identity is revealed to the offering company; the offering company stays anonymous until it accepts | M |
| V-5 | Pool terms | Set by the offering company when accepting: shared trades/equipment, recharge, return guarantee, priority rule, notice | M (simple form) |
| V-6 | Cross-company mechanisms require a link or an operator-run anonymised proposal | Accepting Riverside's crew request makes the link ACTIVE and sends the M8 proposal to Sparks | M |
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
| R-6 | Visible hand-offs | Every cross-party request shows a tracker ("Waiting for Marcus…" → "✓ Marcus · 08:03"); decided items stay listed; counterparties get a notification (bell + unread banner). Trackers never name an anonymous party | M |
| R-7 | Guided demo script | Each script step is clickable (go to it, jump ahead, replay a finished step); the next control to click is highlighted; nothing auto-plays | S |

## 7. MVP for today (the demo story)

Build exactly what makes this story work, end to end, reliably. Each step is a click by the named person; each hand-off is visible to the other side (R-6).

1. **Dan (timeline):** rain risk shows on J1. Dan clicks the J1 bar → Update → finish 235 (or sends the Plaud note) → preview: J1 + 18 downstream steps, handover 397 → 402, **M&E surplus at Site A days 230–235** → Propose.
2. **Dan:** confirms the fact. His tracker shows "Waiting for Priya…".
3. **Priya (Approvals):** approves (handover moved). Dan's tracker shows "✓ Priya". Gap: Sparks S1 idle days 230–235.
4. **Priya (Sync Board):** options M8 (offer the idle days), M3 re-slot, M1 infeasible, M10 for shortages; no action +8 vs with action +5 = **3 days protected**. Priya **offers S1's idle days to nearby projects**.
5. **Marcus (timeline):** banner "M&E crew available near you: 6 workers, days 230–235 · fits your C-K3 first fix" from #4K1. He **requests an anonymised view of #4K1**.
6. **Priya (Requests):** sees "Riverside Construction asks to see Hackney Wick Yard, anonymised" and **shares** it.
7. **Marcus (timeline, Trades view):** overlays #4K1; the offered window lines up with his M&E need; he **requests the crew**.
8. **Priya (Requests):** **accepts and sets terms** (M&E pool, S1 back by day 235). Link ACTIVE; Marcus now sees "Northgate Build"; proposal goes to Sparks.
9. **Sam (Sparks, Proposals):** accepts the move.
10. **Marcus (Reviews):** confirms the S1 booking on C-K3 days 230–235.
11. **Priya (Approvals):** confirms her booking (S1 on A-K3 235–255). Sync done; days protected report shows 3 days, £24,000.

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

## 12. Changes in v2.1

- **Direction of the cross-company flow:** the lender offers, the borrower asks. Replaces "Priya requests to link" with offer (Priya) → view request (Marcus) → share (Priya) → crew request (Marcus) → accept with terms (Priya). The accept replaces the separate "approve M8" step.
- **Timeline-first:** the timeline is every role's home screen and the main way to update (C-0); overlays (V-2c) and anonymised view requests (V-2b) added.
- **Visible hand-offs (R-6)** and a clickable demo script (R-7).
- Implementation impact is listed in `02-technical-spec.md` §13.
