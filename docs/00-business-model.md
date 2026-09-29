# SiteSync: Business Model and Process Flow

| | |
|---|---|
| Status | Working draft. Critical-path context for the pitch and for scoping. |
| Date | 2026-09-29 |
| Feeds | `01-product-requirements.md` (personas, MVP), the demo narrative |
| Note | Competitor and market sizing are being researched separately; add findings in §9. |

## 1. The founder's hypothesis (as stated)

> Project managers share their plan by uploading Plaud voice notes and photos of plans. SiteSync analyses what they need, shows which of their contractors are booked but whose work isn't ready (so they'll sit idle), and offers a marketplace of other developers' contractors. An agent calls both sides to arrange the loan, and the platform handles the paperwork.

## 2. Assessment

**The core loop is right:** capture messy signals → predict the real programme → find the capacity a delay frees or needs → match it → transact. There is a real problem underneath: idle, paid-for labour sits next to sites that are short of the same trade, and nobody can see both at once.

Six things need correcting or sharpening:

| # | Issue | Why it matters | Fix |
|---|---|---|---|
| 1 | **GCs mostly don't own the crews.** On UK residential jobs, most trades (M&E, drylining, groundworks) are subcontractors. The crew belongs to the subcontractor, not the GC. | The GC can't "lend" a crew it doesn't employ. The party that actually redeploys the crew is the subcontractor. | Make the **subcontractor** a first-class participant. The GC *releases* a booking window; the subcontractor *accepts* the redeployment. |
| 2 | **A marketplace on day one has no liquidity.** Matches need several active sites within about 10 km, with the same trade in the same window. | With a handful of users, nothing matches, so nobody stays. | Lead with **single-player value**: a live programme from voice notes and photos, delay prediction and crew impact. That's useful with one user. The marketplace switches on in areas where density exists. |
| 3 | **The best first match is inside your own company.** | Redeploying to your own other site needs no trust, contract or paperwork. | Match in this order: **own portfolio first, then the external marketplace.** |
| 4 | **The demand side has more money than the supply side.** An idle crew costs about £1.2k per day. A site short of a critical-path trade burns its overheads (typically several £k per day) and risks penalty damages for late completion. | Pricing and go-to-market should target whoever feels the most pain. | Charge the **hiring side** (a fee per crew-day filled). Supply-side participation is free, and its incentive is recovering idle cost. |
| 5 | **An AI agent phoning people to close a deal is risky.** Loans involve insurance, site inductions, method statements and liability. People in construction work by phone and WhatsApp, and trust people, not bots. | An agent committing crews without a human in the loop won't be trusted, and may be legally messy. | The agent **prepares and chases; humans accept.** It drafts an anonymised offer, contacts both sides, collects yes/no, and only then reveals identities (double-blind until both accept). |
| 6 | **"The platform does the paperwork" carries regulatory weight.** If SiteSync supplies workers, it may be treated as an employment business (UK Conduct Regulations), with tax obligations (Construction Industry Scheme deductions, IR35). | Becoming an agency on day one is slow and capital-intensive. | Act as a **marketplace facilitator**. The contract is directly between hirer and subcontractor, on SiteSync's standard short-form call-off terms. SiteSync verifies compliance documents and takes a fee. Becoming an agency is a later option, not the start. |

Terminology: say "idle crew capacity" or "spare capacity", not "liquid contractors".

## 3. Improved process flow

```
 CAPTURE        UNDERSTAND       PREDICT         DECIDE (internal)     OFFER (external)      AGREE            EXECUTE & SETTLE        LEARN
 ───────        ──────────       ───────         ─────────────────     ────────────────      ─────            ────────────────        ─────
 Plaud voice ─► LLM extracts ─►  Graph        ─► Resequence, or     ─► Anonymised offer  ─►  Agent drafts ─►  Timesheets by voice ─►  Actual vs
 note, photo    delay/bookings   propagates      redeploy to own       (supply) or need      call-off order,  note, invoice,          predicted
 of labour      → human          delay; crew     other site?           (demand) posted;      checks compliance payment, fee           improves
 plan, weather  confirms (1 tap) impact + £      If not ↓              subcontractor opts in docs; both sides                          prediction
                                                                                              accept; identities
                                                                                              revealed
                                                                  ◄──── Return guarantee: engine checks the loan ends before the crew's
                                                                        rescheduled start at home, and alerts if the home site recovers early
```

Step by step:

1. **Capture.** Site manager records a voice note (Plaud), photographs the labour-plan whiteboard, and the weather forecast is pulled automatically. No forms.
2. **Understand.** An LLM extracts structured updates. A human confirms with one tap. Nothing is written without confirmation.
3. **Predict.** The dependency graph propagates the delay and shows downstream steps, the new finish date, crews newly idle or double-booked, and the £ impact.
4. **Decide internally first.** Suggest resequencing (pull forward a step that is ready) or redeploying to the same GC's other sites.
5. **Offer externally.** If there's no internal use, publish **anonymised** capacity (or an anonymised need). The subcontractor who employs the crew must opt in.
6. **Match.** Rank by trade, window overlap, distance, compliance (insurance, qualification cards), and reliability rating.
7. **Agree.** The agent contacts both sides with a pre-filled offer. Both accept, and only then are identities revealed. A short-form call-off order is generated and compliance documents are checked.
8. **Execute and settle.** The site manager confirms days worked by voice note. SiteSync issues the invoice, handles payment, and takes its fee.
9. **Return guarantee.** The engine checks that the loan ends before the crew's rescheduled start at the home site, and alerts early if the home site recovers ahead of plan. This is what makes a GC willing to release a crew.
10. **Learn.** Actual vs predicted outcomes improve delay prediction per trade, step and weather condition.

## 4. Who pays and why

| Participant | Pain | What they get | Pays? |
|---|---|---|---|
| **GC operations director** (Priya, Marcus) | Programme always stale; idle-crew claims; late finish | Live programme, impact alerts, internal redeploy, access to external capacity | **SaaS per active site**; plus the marketplace fee when hiring |
| **Subcontractor** (M&E, drylining firms) | Paid crews sitting idle when GCs slip; double-booked across clients | Gap-filling work nearby, early warning of slips | Free (supply side). Paid tier later for crew utilisation tools. |
| **Developer** (client of the GCs) | Late completion delays sales and interest costs | Portfolio view of predicted finish across all GCs | **Portfolio licence.** Can mandate that its GCs use SiteSync (top-down distribution). |
| **Site manager** (Dan) | Admin, being blamed for knock-on delays | Report by voice in 20 s; a record that he flagged it | Free, bundled with the GC |

**Revenue mix:** (1) SaaS per active site per month, the reliable base; (2) marketplace fee as a % of crew-day value filled; (3) later, delay-risk data for lenders and insurers.

## 5. Alternative models considered

| Model | Pros | Cons | Verdict |
|---|---|---|---|
| **A. Pure marketplace** (the founder's hypothesis as stated) | Big outcome if liquid; clear fee | Cold start, trust, regulation, GCs don't own crews | Phase 3, not the start |
| **B. Schedule intelligence SaaS** for GCs (single-player) | Valuable with one user; clear buyer; fast to sell | Crowded category (to be confirmed by market research); weaker network effect | **The wedge, phase 1** |
| **C. Subcontractor utilisation tool** (sell to trade firms managing crews across many GCs) | Subcontractors feel idle cost directly; they are the natural supply side | Fragmented SMEs; low software spend | Strong phase 2 route to supply |
| **D. Developer-mandated platform** (developer requires its GCs to use it) | Solves distribution: one sale brings several GCs; developer is a natural neutral party | Longer enterprise sales | **Best go-to-market for phase 1 to 2.** Our demo (one developer's view, two GCs) fits this. |
| **E. Delay-risk data** for lenders, insurers and monitoring surveyors | High value per customer | Needs lots of history | Phase 4 |

**Recommendation:** B + D now (schedule intelligence, sold via developers, used by GCs), C to build supply, A switched on per area once density exists. The fee revenue comes later. The data and the network come from phase 1.

## 6. Phasing

| Phase | Product | Proof point |
|---|---|---|
| 1. Wedge | Voice/photo → live programme → delay and crew-impact alerts → internal redeploy | GCs update programmes weekly with no planner time |
| 2. Network | Anonymised cross-GC capacity offers; subcontractors join to list availability | First filled cross-GC crew-days in one dense area (e.g. East London) |
| 3. Transaction | Agent-assisted agreement, call-off orders, compliance checks, payments, fee | Take rate on filled crew-days; repeat usage |
| 4. Data | Delay prediction models; risk data products | Prediction beats planner estimates |

## 7. Why the tech choices follow from the model

- **Neo4j:** the product is a graph of steps, dependencies, crews and sites. Propagation, clash detection and geo-matching are graph queries.
- **Plaud:** capture has to cost the site manager nothing. Voice is how site staff already communicate.
- **Crusoe:** a neutral broker for competitors' data can't send it to closed-model vendors. SiteSync runs open-weight models on Crusoe (serverless now, dedicated deployment in production). *Check Crusoe's data-handling terms before claiming this on stage.*
- **OpenRouter:** vision for labour-plan photos (if Crusoe can't do it) and demo resilience.
- **Agent with visibility boundaries:** each GC's agent sees only its own data, and a broker agent sees only anonymised offers. This matches BAND's prize criteria ("enforced cross-account or visibility boundaries"). Optional stretch; not in the MVP.

## 8. Implications for the hack day build

Scope does **not** grow. The MVP already demonstrates phases 1 to 2. Changes:

1. **Matching order:** rank own-portfolio matches above external ones (small change to engine §5.6).
2. **Say "subcontractor opts in"** in the anonymised offer card; no new flow is needed.
3. **Return guarantee:** the offer card states "crew back on site A by day 235". The engine already knows this.
4. **Phase 3 in the pitch only:** show one slide or mock of an agent-drafted call-off order. Don't build payments or calling.
5. **Pitch framing:** "Developers mandate it, GCs use it daily because it saves planner time, and the idle-capacity marketplace is the network effect on top."

## 9. Open questions (feed from market research)

- Who already does AI delay prediction and programme tracking, and who (if anyone) does cross-GC crew sharing? Where does SiteSync differ?
- Typical subcontract terms: exclusivity, standby or idle payment clauses, who bears idle cost on a weather delay vs a GC-caused delay?
- Size: number of active residential sites per dense area (e.g. East London), typical crews per site.
- Would developers pay per site, and how much?
- Legal check: facilitator vs employment business in the UK.
