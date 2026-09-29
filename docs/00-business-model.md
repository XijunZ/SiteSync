# SiteSync: Business Model and Process Flow

| | |
|---|---|
| Status | **v5 is current (section "CURRENT MODEL" below).** Sections B, A, 0 onward are the reasoning history that led to it. |
| Date | 2026-09-29 |
| Feeds | `01-product-requirements.md` (personas, MVP), the demo narrative |
| Scope | **Global**: any city with enough concurrent private projects (London, Paris, New York, Dubai, Hong Kong, ...). Nothing here is jurisdiction-specific. |
| Note | Competitor and market sizing are being researched separately; add findings in §11. |

## CURRENT MODEL (v5, agreed in brainstorm 2026-09-29)

**One line:** SiteSync buys GCs time on trade gaps. It warns early, and each extra week of warning unlocks more ways to fill the gap. We list the feasible options per GC with deadlines, run the one the PM approves, and guarantee the crew turns up.

**Founder choice:** design the real business first, then shape the pitch from it. Operating model: a service run with software, plus transactions, growing toward whichever wins (possibly employing workers ourselves). Not pure SaaS. Go-to-market by cold outreach; the founder can reach developers, GCs and subs, lenders and consultants, agencies and plant hire.

**Customer:** the **GC**. The PM is the daily user; the GC signs. Developers and lenders come later as a reporting layer.

**Positioning:** amplify PMs, don't replace them. SiteSync is the PM's capacity desk. It sees what a PM can't (across sites and companies, weeks ahead) and does the chasing they don't have time for. The PM approves; we execute. Analogy: a **freight broker for construction trade capacity** (see both sides of the market, match, guarantee delivery, earn per fill), not an ERP.

**Product loop:**
1. **Early warning** from GC plans (programme, lookahead and labour plan, site manager notes) plus external signals (weather, long-lead items, utilities, inspections). The graph turns one slip into downstream gaps weeks ahead.
2. **Next-best-action engine**: options depend on **lead time**:

| Warning | Feasible options |
|---|---|
| 4+ weeks | Everything, including a **new sub for this GC** (start prequalification now), so cross-company crew moves are viable |
| 1–3 weeks | Sub-tier under an approved sub; pre-agreed framework loans; temporary permits (UAE); slot swaps |
| Under 1 week | Agency labour via the GC's approved list; slot swaps |
| Under 48h | Agency only (where PMs are stuck today) |

   Options are listed **per GC** (its approved subs and agencies, its consent rules, its city's regulations), each with a **start-by deadline** ("start prequalifying Sparks with Riverside by day 205 or this option expires"). Blocked routes are never proposed (licensed-trade payroll rules, unions, for-profit lending, imported labour).
3. **Execute** the approved option via approved channels: slot swap, sub-tier, partner agency, eventually our own workers. Prequalification is paid **once per GC**, then fills are fast.
4. **Guarantee and prove**: turn-up guarantee on critical trades; monthly "days protected × the GC's own day value" report.

**Moat:** each early warning that leads to a prequalification leaves a permanent approved relationship. The network of approved routes compounds, and competitors must redo the paperwork.

**Data from GCs (they are the customer, so they supply it):** programme export (once), weekly labour plan (photo), a 30-second site manager voice summary (Plaud), GC-approved before use. Replaces their site diary and reporting work.

**Pricing (to be finalised later; viable options exist):**
- Day value anchor = the GC's own **daily preliminaries + liquidated-damages exposure**
- Candidate structure: base fee per project per month (as a preliminaries line, so it passes through in tenders; anchored to "less than one day of your prelims per month") + fill margin on labour and equipment routed through us or partners + optional turn-up guarantee premium with service credits
- Success fee used as **proof** (days protected report), not as the main billing
- Avoid: per-alert pricing (rewards noise); per-placement agency referral fees (bias the ranking)

### v5.1 additions (from the product design brainstorm, 2026-09-29)

**Identity:** SiteSync **keeps sites in sync**. It is the next-best-action engine that finds what falls out of sync when a timeline moves (crews, equipment, inspections, bookings, across sites and companies) and runs the mechanism that fixes it. **Not an ERP** (not the system of record) and **not a prediction tool** (the forecast is an input; the product is the action).

**Foundation:** each project's timeline built on its dependency graph, with **labour loading** (planned headcount per step by trade) and bookings. Every change (a human input at any time, or a signal such as weather, strikes or city incidents) propagates through dependencies and recomputes the **labour balance**: which trades now have a **surplus** (booked, no work), a **shortage** (work, nobody booked) or a **clash**. Each new imbalance becomes an out-of-sync gap with its warning time.

**Site-sync mechanisms (the product surface):** a catalogue of playbooks, each with preconditions, setup lead time, parties and outcome tracking. Within site: M1 resequence, M2 mitigate, M3 re-slot trades. Across own sites: M4 crew redeploy, M5 equipment transfer, M6 shared specialists, M7 batched inspections. Across companies: M8 slot swap, M9 sub-tier, M10 agency top-up, M11 early prequalification, M12 local-market routes.

**Three tiers of visibility and the network:**
- **Own company:** full timelines across all its projects
- **Linked partners:** only the shared pool
- **City network:** anonymised timelines of other projects using SiteSync (area, weeks, phase, trade need or surplus windows; no names; minimum-crowd rule; confidential projects excluded)

**Link and pool:** a company can request to link with an anonymised project's company (the requester reveals itself; the target stays anonymous until it answers). On acceptance they agree pool terms (resources, recharge, return guarantee, priority rule), and cross-company mechanisms between them get easier. Each completed sync leaves approved relationships, so the network compounds.

**What this adds to the business model:**
- **Network effects:** every project added makes the city view richer, and more surplus meets more shortage. A dense city is the unit of expansion.
- **The city view as a sales tool:** prospects can see anonymised demand near their sites before joining.
- **A future data product:** anonymised trade × week surplus and shortage heatmaps per city, for agencies, subs and plant hire (a subscription to demand data, not per-placement fees).

**Honest limits:** anonymised demand windows still reveal something about a company's pipeline to competitors (mitigated by coarse data, the minimum-crowd rule and opt-in; answered in the pitch as "you see theirs too, and only linked partners see detail"); cross-company crew moves only work with enough lead time or an existing relationship; peer-to-peer marketplaces failed historically, so we coordinate and fulfil through approved channels; GCs won't share raw recordings (30-second summaries, GC-approved).

## B. Audience and who pays (v4; superseded by the CURRENT MODEL above)

**Problem with v1 to v3:** selling prediction and planning to GCs and subs is a nice-to-have. They already hedge: subs overbook across GCs, and GCs pad their programmes. They won't pay to replace a hedge that works for them.

**Insight: the hedge pushes cost onto the client.** Overbooked subs spread crews thin, which causes under-manned sites, no-shows and slow progress. Padded programmes cause later completion. The **developer** pays every day of delay (construction loan interest, later sales or rent, extended team fees), and has the **worst information**: a monthly GC progress report (optimistic) plus a monthly monitoring surveyor visit.

| | |
|---|---|
| **Customer** | **Property developers**, and the **construction lenders** financing them |
| **Product** | Independent, continuous completion forecast per project: real progress, real finish date, delay cost in money terms, root cause (e.g. "M&E sub overbooked across two GCs"), and the recommended lever |
| **Why they pay** | They bear the delay cost directly, and they're blind between monthly reports |
| **Existing budget** | Lenders already pay monitoring surveyors per project for monthly visits and drawdown sign-off. SiteSync turns that monthly snapshot into continuous verified data, taking an existing budget line. |
| **Pricing** | Per active project per month, or a share of the monitoring budget. High price per customer. |
| **Adoption** | The developer requires it as a contractual reporting obligation in the building contract. Voice notes replace the site manager's written daily report. Subs join free. |
| **Second revenue line** | Early payment to subs on verified progress (fee on financed volume via a finance partner). Subs pay for cash flow, which is their acute pain. |
| **Cross-GC coordination** | A developer contracts all its GCs, so it can see across them and act (e.g. have one GC release the M&E sub for 5 days to another of its sites). The developer is the neutral party with rights to the data. Cross-developer matching comes later, with density. |
| **Stop** | Selling prediction to GCs or subs as a planning tool; leading with idle-crew savings. |

**Pitch:** "Developers lose £X a day on every late site and find out a month later. SiteSync gives them the truth daily, from the voice notes their site managers already send, and tells them which lever to pull."

**Validate in market research (make or break):** do developers and lenders pay for project monitoring today, how much per project, and would they pay for continuous monitoring?

**Hack day demo change (pending approval):** add a **developer view** (all 4 sites, predicted vs contract completion, delay cost at a demo assumption such as £8k per site per day, shown on screen); the root cause and recommended lever are shown there. Keep GC views for neutrality.

### B.1 Worked example: how money is actually saved (the product is "delay response", not a forecast)

A forecast alone saves nothing. Money is saved by **actions taken early enough to matter**. For each predicted delay, the product shows actions in order: **prevent → resequence → redeploy → notify**, each with its conditions and a £ value for the party that benefits.

**Scenario** (demo numbers; costs are illustrative assumptions): Site A (Northgate) roof slips 5 days due to rain, so M&E first fix moves from day 230 to 235. Sparks Ltd (M&E sub, 6-person crew) also works for Riverside, whose Site C first fix (days 225–245) is critical. Crew-day £1.2k; developer delay cost about £8k per site per day.

**Without SiteSync** (Sparks learns on day 229): either (a) the crew waits, and Sparks eats £6k and prices the risk into future tenders; or, more commonly, (b) the crew goes elsewhere and returns on day 238, so **A finishes +8 days instead of +5**: about £24k extra for developer A, plus penalty or dispute exposure for Northgate. This is the overbooking hedge turning a 5-day delay into 8.

**With SiteSync** (flagged on day 220): try to prevent it first (start the roof 2 days early, temporary cover); if not, offer Sparks' free days to Site C with a return guarantee for day 235, provided C has a separate floor for a second crew; tell A's downstream trades their new dates immediately.

| Pot | Saving | Whose | Condition |
|---|---|---|---|
| Knock-on on A avoided (crew back on 235, not 238) | about £24k | Developer A | M&E on A's critical path (true in our programme) |
| C sped up (5 extra crew-days on a 20-day task) | up to about £40k | Developer C | C's M&E critical, space for a second crew, early finish has value |
| No idle crew | £6k | Sparks (and developers, through lower risk pricing) | — |
| Delay prevented | whole cost | Developer A | Cover or resequencing feasible |

**Pattern:** the developer's day of delay (£8k+) dwarfs the crew-day (£1.2k). The biggest reliable saving is stopping a small delay from cascading into a bigger one, via a reliable crew return. Selling idle capacity is secondary.

**Limits:** the saving needs the work on the critical path, space at the receiving site, an existing sub relationship with both GCs (L2), and about a week's notice. The product must say "no action worth taking" when these fail. Savings are counterfactual, so charge a subscription and report "days protected" (calculated by the graph) as proof of value, not a success fee.

**Demo money line:** "Weather: roof +5 days. No action: M&E return clash, A finishes +8 days (£64k). With action: +5 days (£40k), so £24k protected. Site C gains up to 5 days."

### B.2 Why the developer cares when subs are paid for work done

How M&E is paid (for completed work) decides who bears the **labour** cost of a delay. The developer bears the **time** cost regardless:

| Cost to developer | Why it runs per day |
|---|---|
| Loan interest | Accrues on nearly the full drawn loan (mostly drawn by fit-out) until sales or refinance |
| Loan deadlines | Completion dates in the facility; extension fees or default |
| Revenue delay | Build-to-rent: rent starts later. Off-plan: completions move later, and buyers can walk away after longstop dates. |
| Pre-let penalties | Tenants can claim compensation or terminate |
| Extended team and site costs | Professional fees, insurance, security run longer |

**Why liquidated damages don't solve it:** (1) weather is typically an excusable event, so the GC gets extra time with no damages and the developer bears the weather delay in full; (2) cascade delays (crew return clash) are the GC's risk, but damages are usually set below the real loss, often capped, and frequently disputed; (3) delay risk is priced into tenders anyway.

| Slice (our example) | Who really pays |
|---|---|
| 5 days of weather | Developer (time cost; GC gets extra time) |
| +3 days of cascade | GC (damages exposure) and developer (loss above damages, plus the dispute) |
| Idle crew | Sub |

**Pitches:** to developers and lenders: "Contractors get paid for work done, but the finance clock runs on the building. Delay damages don't cover your real loss, and weather isn't covered at all." To GCs (secondary buyer): "Avoid the damages you'd pay for cascading clashes."

**Segment:** leveraged projects with revenue deadlines (build-to-rent, off-plan residential, pre-let commercial, lender-financed). Cash-funded developers with no sale dates care much less.

**Research:** developers' daily delay cost at different project sizes; how often liquidated damages are actually recovered.

### B.3 "Why not just push the GC hard?" and who actually buys

**Do developers pay to catch up?** Often. For excusable delays (weather, design changes, late information) the GC is entitled to extra time; keeping the original date means **instructing and paying for acceleration**. Refusing the extension while demanding the date leads to a claim that the developer forced acceleration. For GC-caused delays, the GC recovers at its own cost or pays damages, but passes pressure down to subs.

**Why pressure alone fails:** (1) you can't pressure what you can't see (monthly reports arrive weeks late; by then catching up means paid acceleration); (2) pressure doesn't create crews (squeezed subs overbook more and deprioritise); (3) pressure without evidence becomes a dispute (weather vs GC fault).

**Positioning:** not "software instead of pressure" but **"pressure earlier, on the specific cause, with evidence"**. E.g. "Your M&E sub is double-booked with another client days 230–250 and will return 3 days late. Fix it this week." Weather days documented as excusable, cascade days as the GC's.

**Buyer (revised): whoever the developer already pays to do the pressuring.**

| Buyer | Today | SiteSync value |
|---|---|---|
| Developer-side project managers / employer's agents (consultancies) | Monthly visits and reports, chasing GC | Earlier specific issues; more projects per person; better margins |
| Monitoring surveyors (for lenders) | Monthly visits, drawdown sign-off | Continuous evidence between visits |
| Claims and cost consultants | Reconstruct delay causes months later | Timestamped cause and effect as it happens |
| Lenders and institutional developers (BTR operators, funds) | Portfolio risk | Early warning across projects |

Developers themselves rarely want to operate software; they get the benefit through their consultants. **Research test:** would developer-side PM or monitoring-surveyor firms pay per project? Fallback buyer: GCs (avoid delay damages).

### B.4 The offer and pricing (current summary)

**Offer:** a tech-enabled **managed service**, a "delay response desk". The developer requires its GCs to share data (programme, weekly labour plans, daily voice notes). SiteSync runs early warning plus a next-best-action engine, with a person on our side confirming actions, chasing GCs and reporting weekly. Over time the engine does more, so each person covers more projects and margin grows.

**Pricing: hybrid shared savings** (the pattern is borrowed from energy-efficiency contracts: fees tied to measured savings against an agreed baseline):

| Element | Rule agreed at onboarding |
|---|---|
| Base fee | Per project per month; from the monitoring or project management budget; covers cost and cash flow |
| Success fee | % of **verified days protected × agreed daily delay cost** |
| Baseline | Engine's "no action" forecast **locked and timestamped** when the warning is issued |
| Attribution | Counts only when a recommended action was taken by the parties (logged) |
| Measurement | Per event: locked no-action forecast minus the post-action forecast, confirmed by actual progress; **settled monthly**, not at completion |
| Cap | Success fee capped per project |

Why not pure %-of-savings: the counterfactual is disputable, attribution is unclear, cash arrives at completion (18–24 months), and there's an incentive to inflate baselines. The hybrid fixes all four.

**Example:** warning on day 220, locked no-action forecast A = +8 days; the action (crew back by 235) is taken; post-action forecast = +5, so 3 days protected × £8k = £24k. At a placeholder 10–20%, the fee is £2.4k–£4.8k, invoiced that month.

**Demo:** show the locked no-action forecast next to the with-action forecast, plus "3 days protected · £24k · fee £X". Needs two propagation runs and one stored snapshot.

### B.5 Stress tests (hypotheses to verify in market research)

**1. Multi-site developers in one city.** By number of developers, most are small (1 to 2 projects); by share of activity, repeat multi-site players are often significant. Varies by city: Dubai and Hong Kong are dominated by large groups with many concurrent projects; London and Paris are mixed (housebuilders, BTR operators, housing associations, plus a long tail); in New York projects sit in separate companies but sponsors repeat. **Stress point:** even a 4 to 6-site developer rarely has two sites needing the same trade in the same window nearby, so within-developer matching is thin. **Conclusions:** (a) the core service (early warning, prevent, resequence, notify, protect crew returns) must work on a single project, and that's where the base fee is earned; (b) matching density comes from the **channel**: a monitoring surveyor firm or lender covers many projects across many developers in a city, so it's the natural aggregator and the preferred first buyer.

**2. Will GCs share start-of-shift recordings?** Raw recordings: probably not (dispute exposure, privacy and consent law such as GDPR and all-party consent states, culture). Design for compliance:
- The site manager records a **30-second summary**, not the meeting (no workers recorded)
- **GC reviews and approves** the extracted update before sharing; audio stays with the GC or is deleted after transcription
- It **replaces the GC's own reporting** (auto site diary and monthly report)
- **Shared neutral record:** weather and developer-caused delays documented as they happen support the GC's own extension claims
- **Contractual reporting clause** from the developer

**Pitch correction:** replace "evidence of GC fault" (§B.3) with "one neutral record that protects everyone". **Fallback:** the forecast degrades gracefully without voice notes, using weather, access-control headcounts, deliveries, photos, public inspection and permit records, and monitoring visits.

**Validate:** share of active sites held by multi-site developers per city, and projects per monitoring surveyor firm per city; interview 3 to 5 GC managers ("30-second daily summary if it replaced your diary and you approved what's shared?"); do contracts already require daily records or diary access?

### B.6 Practical resource sharing between sites (easiest first)

| # | Mechanism | How | Why it's practical |
|---|---|---|---|
| 1 | **Slot swap** with a shared subcontractor | Same sub works both sites; A slips, C is ready, so the sub does C first and returns to A on a fixed date | No new contracts, just date changes under existing subcontracts. **This is the demo scenario.** |
| 2 | Equipment and plant (hoists, telehandlers, lifts, generators, cabins) | Off-hire at A / on-hire at C via the same hire company, or a direct internal move | Transfer business already exists; no employment or qualification issues |
| 3 | Temporary works and surplus materials (props, formwork, scaffold, blocks, board, cable) | Transfer at cost with a recharge | Cuts urgent lead times and waste; ESG and carbon angle |
| 4 | Shared specialists (commissioning, fire-stopping, building safety manager, clerk of works) | One specialist scheduled across nearby sites | Already employed or appointed; a scheduling problem, not a contract one |
| 5 | Batched inspections and approvals | Several nearby sites on one inspector visit; pre-booked from the forecast | Attacks a known delay cause ("late inspector stalls drylining") |
| 6 | Shared logistics | Consolidated deliveries, waste haulage, staging yard | Consolidation centres already exist in dense cities |
| 7 | Framework call-offs | Developer sets up frameworks with preferred subs across all its sites | Turns new-relationship matches into existing-relationship matches (the "pre-qualified bench") |
| 8 | Pooled flex crew | Retained crew shared across sites | Hardest: someone funds the retainer and manages utilisation |

**Correction on #1:** slot swaps don't bypass qualification. They apply **only where the sub is already contracted on both sites** (L2), so qualification already exists. New sub-to-GC relationships (L3) still take 1 to 4 weeks and stay out of scope. This narrows labour sharing to a subset of delays (same sub, both sites, overlapping windows, within reach). It may not be tiny: common-trade subs hold contracts with several GCs at once, and multi-site developers reuse subs across sites. SiteSync only suggests swaps where labour plans show the relationship exists. Frameworks (#7) create relationships ahead of need. Non-labour sharing (#2 to #6) needs no sub qualification, so it's more dependable. **Labour sharing is a bonus lever, not the core**; the core (warn, prevent, resequence, protect returns, notify) works on a single project. **Validate:** how many GCs does a typical M&E or drylining sub serve at once per city, and how often do nearby active sites share a sub?

**Rules for any sharing:** return guarantee; critical path wins ties; recharge at rates agreed at onboarding; liability follows the existing contract or hire agreement; savings shared or logged.

**Order for SiteSync:** slot swaps → equipment, plant, temporary works → specialists and inspections → framework call-offs → flex crew.

**Demo:** rename the offer card to "Slot swap: Sparks M&E does Site C first (days 230–235), back on Site A on day 235". Equipment and inspections go on the roadmap slide. In the data model, equipment is just another resource node with a booking window.

### B.7 Research update on labour mobility (supersedes the qualification claims in §4.1 and #1 in §B.6)

Full findings: `04-labour-mobility-research.md`. Summary:
- **Workers can move fast (same day to 3 days) in every market studied** when they already hold their site credentials (CSCS, SST card, carte BTP, HK registration and Green Card). Credentials are portable and belong to the worker.
- **Fast legal routes:** agencies and manpower suppliers (all markets); labour-only gangs (UK CIS, HK gang leaders); sub-tier under a subcontractor already approved on the destination site (with written consent); UAE temporary work permit (about 1 week); French intérim.
- **Slow:** new company-level subcontractor approval (1 to 6+ weeks). **Blocked:** licensed trades tied to the licensee's payroll (NYC), union jobs, imported labour (HK), for-profit lending outside agencies (France, Germany).
- **Commercial lessons:** employer-of-record staffing works (25 to 35%+ margins); peer-to-peer equipment and skilled-labour marketplaces failed or were absorbed. Closest comparables: SmartBench (US), Sukedachi (Japan).

**Model changes:**
1. SiteSync does not employ or broker labour. **Agencies, manpower suppliers and rental companies are fulfilment partners.**
2. **New revenue line: referral and partner fees** when a predicted need is filled through a partner. Agencies value the 1 to 3 week demand signal, which only SiteSync has.
3. The next-best-action engine chooses a **fulfilment route per market**: slot swap → sub-tier under the approved sub → approved sub adds agency labour → temporary permit or at-cost framework loan → equipment via rental partner. It checks a per-market compliance list and never proposes a blocked route.
4. Stage 2 "pre-cleared pools": credentials verified ahead, frameworks and consents pre-signed.

**Who contracts agencies:** almost always the **GC** (its own direct labour, often via preferred-agency frameworks or a managed service provider) or the **subcontractor** (topping up its trade crews). Developers rarely do, because it would take on site-safety and employment liabilities handed to the GC. Exceptions: construction-management procurement, small developers acting as their own contractor, post-handover work.

**Implications:**
- The forecast goes to the developer side; the recommended action (e.g. "add agency labour") is addressed to the GC's or sub's planner. The developer sees the recommendation and whether it was taken.
- Route to the **GC's existing agency frameworks** first. This limits per-placement referral revenue.
- **Conflict of interest:** the developer pays for neutral recommendations; agency per-placement fees would bias the ranking. Keep the ranking transparent, and prefer agencies paying for **demand-signal data access** (subscription) over per-placement referral fees.

## A. The business in one page (v3)

**SiteSync is the readiness and coordination network for construction.** One shared, predicted schedule across developer, GCs and subcontractors, fed by voice notes and photos, that removes delays before they hit. Crew matching is one module, not the company.

### A.1 Root causes of delay, and the SiteSync lever for each

| Cause | Lever |
|---|---|
| Work area not ready for the next trade (prerequisites missing) | **Make-ready agent** (A.2 #1) and **readiness handshake** (#2) |
| Long-lead items and utilities | **Long-lead watch plus network lead-time intelligence** (#6) |
| Approvals and inspections | Make-ready agent books and chases inspections ahead (#1) |
| Weather | **Weather-aware resequencing** (#4) |
| Trade no-shows, crew availability | Readiness handshake (#2); **crew and equipment sharing** (#5) |
| Optimistic planning | **Realistic durations from the network** (#3) |
| Cash flow and disputes | **Early payment on verified progress** (#7); timestamped delay record |

### A.2 Seven levers

1. **Make-ready agent (the biggest lever).** Two to three weeks before each step, check prerequisites (earlier work, materials, inspection booked, drawings approved, scaffold signed off) and chase each owner by WhatsApp or voice. Automates the "make-ready" step of Last Planner, which sites run manually and inconsistently. Prevents delay rather than reacting to it.
2. **Readiness handshake.** The finishing trade confirms "area ready" by voice or photo, and only then is the next crew told to come ("don't come Tuesday, come Thursday"). Fixes no-shows and wasted trips from both sides.
3. **Realistic durations from the network.** Anonymised actuals across all sites give realistic durations per step, trade, city and season, and 50% and 80% likely finish dates instead of a single date. Needs the network; it's the data moat.
4. **Weather-aware resequencing.** Several days before forecast rain, suggest swapping weather-sensitive work with an indoor task that's ready.
5. **Crew and equipment sharing.** Same-sub crews across GCs (L1/L2), plus **idle plant and equipment** (hoists, scaffold, telehandlers). Renting equipment between companies is normal and far less regulated than labour.
6. **Long-lead watch.** Track utilities, windows, lifts and kitchens from supplier emails and notes; learn real lead times per utility and area across the network, and warn new projects on day one.
7. **Early payment on verified progress.** Voice notes and photos build a verified record of work done. A finance partner pays subs early against it for a small fee, so cash-starved subs don't slow down. The same record makes delay claims factual.

### A.3 Revenue layers

| Layer | Product | Revenue |
|---|---|---|
| Core | Programme from voice/photo → forecast → make-ready agent → readiness handshake | Subscription: developer portfolio licence, plus GC per active site. Subs free. |
| Network | Realistic durations, finish-date ranges, lead-time intelligence, crew and equipment sharing | Higher tier |
| Transactions | Early payment on verified progress; later, agreed crew and equipment moves | Fee on finance volume and on filled crew or equipment days |
| Data | Delay risk by trade, city, season, utility | Sold to lenders, insurers, monitoring surveyors |

**Why this beats a crew marketplace alone:** single-player value from day one (make-ready, handshake); a network effect without needing a marketplace (every site improves everyone's forecasts); crew matching is a module; finance gives revenue that scales with activity.

**Story:** make-ready **removes** causes → forecast **predicts** what's left → matching **recovers** idle capacity → early payment **keeps subs working**.

### A.4 Hack day

MVP scope unchanged; it demonstrates the forecast and matching layers. Optional cheap addition: one **make-ready moment** (rule plus one LLM message, e.g. "first-fix inspection for Site A not booked; needed by day 247"). Layers 3 and 4 go on the roadmap slide. The make-ready agent is the natural fit for the BAND agent-coordination prize if pursued later.

## 0. Feasibility in one paragraph

A subcontractor's workers are its own people (employees, or its regular self-employed gang), and subs routinely move them between contracts they hold with different GCs. That is normal, legal, daily practice. SiteSync does not supply, lend or move workers, and workers do not freelance through it. It **forecasts** when a sub's booking will slip and when another site it already works for will be ready, and **introduces** the opportunity weeks earlier than the sub would find out today. The sub moves its own crew under its existing contracts. Out of scope because it's a regulated, different business: freelance labour marketplaces, GCs lending direct staff, and short-notice new sub-to-GC relationships. The real risks are commercial (GC adoption, and whether 2 to 4 weeks' notice fills gaps that 1 to 2 days can't), not legal.

## 1. Positioning (decided)

**Stage 1 is proactive prediction and cross-company matching, not a marketplace.** SiteSync predicts, weeks ahead, which crews a delay will leave idle and which sites will need that trade in that window, across companies. It then makes a warm, double-blind introduction. Humans agree terms and contract **off-platform** using the relationships and contracts they already have. There are no payments, no contracts and no platform-issued paperwork in stage 1.

The value is **lead time**. Today a GC finds out a crew is idle on the morning it turns up to a site that isn't ready. SiteSync tells them two to four weeks earlier, when redeploying is still easy.

## 2. Key data inputs

| Tier | Input | Typical source | Frequency | What we get from it | Stage 1? |
|---|---|---|---|---|---|
| 1 | **Baseline programme** | GC's planning tool export: MS Project (XML), Primavera P6 (XER), Asta Powerproject; or a PDF/Excel Gantt | Once, then on re-baseline | Steps, durations, dependencies, trade packages, planned dates | **Yes** (one import per site) |
| 2 | **Lookahead / weekly labour plan** | 3 to 6-week lookahead meeting, weekly work plan (Last Planner style), whiteboard or Excel of which subcontractor is on which area this week | Weekly | Which subcontractor crew is booked where, and when | **Yes** (photo of whiteboard or sheet) |
| 3 | **Start-of-shift briefing / daily huddle** | Site manager's morning briefing and toolbox talk, often spoken, rarely written down | Daily | "Roof delayed, rain, five days"; "M&E short two people"; "scaffold not signed off" | **Yes** (Plaud voice note) |
| 4 | Site diary / daily report | Site manager's end-of-day report (required on most jobs) | Daily | Labour headcount by trade, weather lost time, instructions | Later (voice or photo, same pipeline) |
| 5 | Attendance / access control | Turnstile or biometric gate systems log workers by employer | Real time | *Actual* crew presence by subcontractor. The ground truth for idle vs working. | Later (integration) |
| 6 | External | Weather forecast; delivery schedules; inspection bookings | Daily | Weather-driven risk on weather-sensitive steps; material-driven delays | Weather: yes, light |
| 7 | Commercial | Subcontract sums, payment applications, daywork rate schedules (held by the GC's commercial or QS team) | Monthly | What idle time actually costs | **No.** Use benchmark rates (below). |

**Where "planned contractor work" comes from:** the baseline programme (tier 1) says *which trade* does *which step* and *when*. The lookahead / labour plan (tier 2) says *which subcontractor's crew* is actually booked. Stage 1 needs tiers 1 to 3; tiers 1 and 2 are low-effort (one import plus a weekly photo), and tier 3 is the daily habit that keeps the prediction live.

**Where "how much they're paid" comes from:** we don't need contract sums in stage 1, and GCs won't share them early. We use a **benchmark crew-day cost per trade per city** (e.g. published daywork or labour rates), editable by the customer. This is only used to size the prize ("£6k of idle M&E"), not to bill anyone.

## 3. How subcontractors are paid, and who bears idle cost

This decides who feels the pain, so who pays SiteSync.

| Contract basis | How it works | Who bears idle time from a delay |
|---|---|---|
| **Lump sum / measured package** (most common for trade packages) | Fixed price for the package; paid in periodic (usually monthly) valuations of **work done**, less retention | **The subcontractor**, unless they can prove the GC caused it and claim through the contract's delay and cost mechanism. Neutral events such as weather usually give extra time but not money, so the sub absorbs the cost. |
| **Labour-only / day rate / daywork** (common for labour supply in many markets, e.g. the Gulf, parts of Asia, and small works everywhere) | Paid per worker-day attended | **Mostly the subcontractor**: no attendance, no pay. Some agreements include a standby rate, which the GC then bears. |
| **Cost-plus / time and materials** (some US and fit-out work) | Paid actual cost plus a fee | **The client or GC**: idle time is billed through |

Standard contract families differ by region (for example JCT/NEC in the UK, FIDIC across the Gulf and Asia, AIA/ConsensusDocs in the US), but the pattern is the same.

**On reservation fees:** in most markets there is no explicit fee for holding a crew's time. Subcontractors manage the risk **exactly as suspected**: they keep a pipeline across several GCs, overbook slightly, move crews between clients themselves, and price the risk into their rates. When a GC slips, the sub's own planner scrambles to find the crew work elsewhere, by phone, with a day or two of notice.

**So:**
- The **subcontractor** is the party most often losing money when a GC slips. They are already doing the matching manually, with poor visibility and no notice.
- The **GC** loses when the delay is its fault (claims), and when a critical trade is unavailable (its site overheads keep running).
- The **developer** loses when completion slips (finance costs, delayed sales or rent).

### 3.1 Value by party (why each would actually use it)

The fact that subcontractors bear idle cost does **not** by itself mean SiteSync helps them. Subs already hedge by overbooking across GCs. The question is what they still lose despite that hedge.

**Subcontractor: what the hedge doesn't fix, and what SiteSync adds**

| Still losing | Why | SiteSync gives |
|---|---|---|
| Unfillable gaps | Slips are learned with about 1 to 2 days' notice, too late to redeploy | A 2 to 4-week forecast of when each GC will *actually* need them |
| Clashes | Overbooking backfires when two GCs' dates line up, so a crew gets pulled, with penalties and lost goodwill | Early clash warnings, so less overbooking is needed |
| Unrecovered cost | Idle cost is the sub's unless they can prove GC fault, and they rarely have evidence | A timestamped delay record: who flagged what, when, and why |
| Planner time | Hours phoning sites to find out what's really ready | One view across all their GCs |

**Limitation:** subs only get this if their GCs use SiteSync, because the forecast comes from GC data. Subs are **beneficiaries and the network, not stage 1 buyers.**

**GC: the mirror image of sub overbooking.** The GC's pain is not mainly idle cost (under lump-sum terms that's the sub's). It is: **when my site is ready, the crew isn't there**, because the sub moved them after losing trust in my dates.

| GC value | How |
|---|---|
| Crews turn up when the site is ready | Reliable forecasts shared with subs; return guarantee ("back on site A by day 235") keeps subs committed |
| Being the GC subs prioritise | Reliable GCs get the best crews and better prices |
| Fewer disputes | A shared delay record reduces idle-cost claims arguments |
| Planner time | Programme updated from voice notes and photos |

**Developer:** fewer critical-path delays, which means earlier completion and lower finance costs.

**Pitch, corrected:** coordination, not idle-cost savings. *"SiteSync gives GCs and their subcontractors one shared, predicted schedule, so crews are there when sites are ready and aren't wasted when they're not."* Cross-company introductions resolve the idle side.

**Demo implications:**
1. Label £ on the GC alert as "idle cost at risk (borne by your subcontractor under lump-sum terms)". The GC's headline is the return guarantee.
2. Add a third view, "M&E subcontractor", showing its bookings at both GCs, the new gap and the lead that fills it. The idle crew becomes the shared `IND-mep` (L2 story). *Pending approval.*

## 4. Matching levels (what "match" means)

| Level | Match | Trust / paperwork needed | Already done today? | Stage 1 |
|---|---|---|---|---|
| L0 | **Resequence**: pull forward another ready step on the same site for the idle crew | None | Sometimes, by an experienced site manager | Yes (suggestion) |
| L1 | Same GC, another of its sites | None | Partly. The ops director knows her own sites, but finds out late. | Yes, but not the headline |
| **L2** | **Same subcontractor, a different GC's site** (the sub already works for both) | **None new**: both contracts already exist | Yes, by phone, reactively, with 1 to 2 days notice | **Yes, the headline.** Most realistic, lowest friction. |
| L3 | A new subcontractor for a GC it has never used | New subcontract, onboarding, compliance | Rarely, in a crisis | Introduction only; parties contract themselves |

**On "within the company, people can already do that":** mostly true for L1, which is why it isn't the headline. What nobody can do today is **L2 and L3 with weeks of notice**, because no one sees across companies. So cross-company **is** in stage 1. SiteSync predicts and introduces; the parties close the deal themselves.

**L2 changes the design:** the subcontractor is a user, not just a data point. A sub's planner sees "your M&E crew's booking at a GC slips 5 days from day 230", plus anonymised demand that fits the gap from other GCs it already works for (and, opt-in, ones it doesn't).

### 4.1 Qualification lead time decides what's viable

Typical ranges from general industry practice. Verify per city in market research.

| Layer | What | Typical time |
|---|---|---|
| Company prequalification (once per sub per GC) | Insurance, H&S record, financial checks, references, licences and accreditations (vary by city); sometimes **client approval** of new subs | 1 to 4 weeks (faster via shared prequalification databases) |
| Contract (per engagement) | New subcontract vs a new order or variation under an existing one | Days to weeks (new) vs hours to a day (existing) |
| Project and worker onboarding (per site) | Method statements and risk assessments approved; per-worker site induction; worker cards and permits (e.g. site safety cards, worker registration; **Gulf work permits may be tied to the employer**) | 1 to 3 days |
| Per-move overhead | Mobilise, induct, hand over, pack up | About 1 to 2 days of the window |

**Viability of a short-notice move:**

| Level | Time to working | 5-day gap, 10 days' notice |
|---|---|---|
| L1 same GC | Hours | Viable |
| **L2 same sub, existing GC relationship** | Hours to 2 days | **Viable** |
| L3 new relationship | 1 to 4+ weeks | **Not viable.** Only for longer windows with long notice. |

**Legal framing, everywhere:** always "the subcontractor takes a short scope at GC B's site" (the sub directs its own crew). Never "GC A lends its crew" (labour supply is regulated as agency work in many countries; e.g. France prohibits lending staff for profit outside temp agencies).

**Rules for the product:**
- Propose a match only if **notice ≥ onboarding time for its level** and **window ≥ minimum** (e.g. 3 days at L1/L2, 10+ at L3). Show L3 opportunities that fail the rule as "worth pre-qualifying for next time".
- **Stage 2 feature and moat: a pre-qualified bench.** SiteSync holds a portable prequalification profile per sub (documents, insurance expiry, worker cards). GCs pre-approve nearby subs before they're needed, which turns L3 into L2 over time.

**Demo consequence:** the current demo match (Northgate's own M&E crew → Riverside, 10 days' notice, 5-day gap) is L3 and not realistic. Switch the idle crew to the shared M&E subcontractor (`IND-mep`) so the match is L2.

## 5. Density check (does a city have enough overlap?)

Founder's estimate: a city with 80 to 100 active private projects has 3 to 5 at a similar stage.

Rough check with our reference programme (52 on-site steps, about 385 working days): M&E first fix runs about 40 days, roughly 10% of the programme. With 100 active projects spread evenly across stages, about **10 are in M&E first fix at any time**, and about 3 to 5 of those are within a practical travel radius of any given site. **The estimate holds** for common trades (M&E, drylining, groundworks, concrete, bricklaying). It's thinner for specialist trades (lifts, piling, cladding).

**Distance should be travel time, not km.** 10 km means very different things in Hong Kong, Dubai and New York. Match within something like 45 minutes by the crew's usual mode of travel.

## 6. Who pays (revised)

In stage 1 there is no transaction to take a fee from, so stage 1 revenue is subscription:

| Customer | Buys | Why |
|---|---|---|
| **Developer** | Portfolio licence covering all its sites and GCs | Sees predicted completion across its GCs; can **require** its GCs to use SiteSync. One sale brings several GCs (distribution). |
| **GC** | Per active site per month | Live programme from voice notes and photos with no planner time; weeks-ahead crew-impact alerts. |
| **Subcontractor** | Free in stage 1; paid "utilisation" tier later | Early warning of slips across all its GCs; gap-filling leads. Free, because subs are the network. |

**Later (stage 3), follow the value:** the party who *recovers* money pays a success fee. That's usually the subcontractor who fills a gap it would otherwise have eaten, or the GC who gets a critical trade it couldn't find. Which side pays in each market is a research question (§11). The earlier "charge the side that needs the crew" assumed a transaction and is withdrawn for stage 1.

## 7. What the agent does, exactly

One agent system with separate roles. Each role sees only what that party is allowed to see.

| Role | Does | Doesn't |
|---|---|---|
| **Listener** | Takes in Plaud voice notes and labour-plan photos; extracts structured updates; **asks the site manager back** when unsure ("Is the five days for roof waterproofing or all roofing work?"); gets one-tap confirmation | Write anything unconfirmed |
| **Forecaster** | Re-runs propagation daily; watches weather for weather-sensitive steps; flags crew gaps and clashes 2 to 4 weeks out; estimates idle cost | Change the baseline programme |
| **Matchmaker** | Ranks options L0 → L3; checks the **return guarantee** (crew is back before its home step restarts); writes each party's alert from only that party's data | Reveal one party's data to another |
| **Introducer** | Sends double-blind "possible fit" messages to the sub's planner and the other GC's ops lead (WhatsApp, email, in-app); collects yes/no; **when both say yes, shares contact details** and a one-page summary (trade, window, site area); follows up after the window to record the outcome | Negotiate price, sign contracts, move money, place phone calls (stage 1) |

The outcome record ("did the introduction happen, did the crew go") trains the next stage and becomes the proof point for investors.

## 8. Process flow (stage 1)

```
 CAPTURE            UNDERSTAND         PREDICT             MATCH                  INTRODUCE              LEARN
 ───────            ──────────         ───────             ─────                  ─────────              ─────
 Baseline (once) ─► Listener        ─► Forecaster       ─► Matchmaker          ─► Introducer          ─► Outcome
 Weekly plan photo  extracts, asks     propagates delay;   L0 resequence,         double-blind          recorded;
 Daily Plaud note   back if unsure;    crew gaps and       L1 own sites,          "possible fit" to     prediction
 Weather            human confirms     clashes 2-4 wks     L2 same sub, other GC, both sides; on        and matching
                                       out, £ impact       L3 new partner;        mutual yes, share     improve
                                                           return guarantee       contacts. Humans
                                                                                  contract off-platform.
```

## 9. Global design principles

- **Nothing jurisdiction-specific in stage 1**: no contracts, payments or employment status. That's why stage 1 can launch in any city.
- **Per-city configuration**: currency, benchmark crew-day cost per trade, working calendar (working days, weekends differ, e.g. Gulf vs Europe), travel-time model.
- **Language**: site briefings happen in the local and site languages (French, Cantonese, Arabic, Hindi/Urdu, Spanish, ...). Plaud transcribes 112 languages, and the extraction model must handle multilingual input. This is a real reason to test open models on non-English notes.
- **Confidential projects**: any project can be flagged **never offer, never match**. Government, defence, security-sensitive and other confidential projects are excluded by default. Their data can still power that customer's own predictions.
- **Neutrality**: each party sees only its own data plus anonymised opportunities, enforced in code and in prompts, with open-weight models on Crusoe so competitors' data isn't sent to closed-model vendors.

## 10. Phasing (revised)

| Stage | Product | Revenue | Proof point |
|---|---|---|---|
| **1. Predict + introduce** | Voice, photo and programme → live forecast → crew gaps 2 to 4 weeks out → L0 to L3 matches → double-blind introductions | Developer and GC subscriptions | Introductions accepted; crew-days recovered (self-reported, then verified by attendance data) |
| 2. Subcontractor network | Subs join directly; utilisation dashboard across all their GCs; list spare capacity | Paid sub tier | Share of matches at L2/L3; sub retention |
| 3. Transaction (market by market) | Agent-assisted terms, standard call-off order templates per region, compliance-document checks, payments | Success fee, following the value | Take rate; repeat usage |
| 4. Data | Delay prediction per trade, step, weather and city; risk data for lenders and insurers | Data products | Prediction beats planner estimates |

## 11. Open questions (for market research)

1. Competitors: who does AI delay prediction or programme tracking, who does crew or labour sharing, and does anyone predict cross-company crew gaps?
2. In each target city: the dominant subcontract basis (lump sum vs labour-only), and whether standby or reservation payments are common.
3. Who really feels idle cost most in practice (sub vs GC), and would they pay for early warning?
4. Density per city: active private projects, and how clustered they are.
5. Will GCs share lookahead plans if the developer mandates it? Will subs join if it's free?
6. What travel time do crews accept for a short redeployment?

## 12. Implications for the hack day build

Scope does not grow. Changes:

1. **Tell the story as L2.** Consider making Site A's idle crew the **independent M&E subcontractor** (`IND-mep`), so the headline match is "your sub has a 5-day gap and already works for another GC nearby". It's the most realistic stage 1 match, and neutrality between GCs still holds. *(Decision needed; it changes seed crew assignment and the demo numbers.)*
2. **Rank matches L0 → L3** in engine §5.6. Show the level on the card.
3. **Offer card** shows the return guarantee ("back on site A by day 235") and "introduction only; you agree terms directly".
4. **Listener asks back** when unsure: already covered by "return candidates if ambiguous" in the spec; show it once in the demo if time allows.
5. **Travel time**: keep km for the demo (straight-line distance), and say "travel time in production".
6. **Pitch:** "SiteSync gives contractors two to four weeks' warning of idle crews and introduces them to a nearby site that needs them, across companies, without anyone seeing anyone else's programme."
