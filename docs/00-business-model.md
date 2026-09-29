# SiteSync: Business Model and Process Flow

| | |
|---|---|
| Status | Working draft v2. Critical-path context for the pitch and for scoping. |
| Date | 2026-09-29 |
| Feeds | `01-product-requirements.md` (personas, MVP), the demo narrative |
| Scope | **Global**: any city with enough concurrent private projects (London, Paris, New York, Dubai, Hong Kong, ...). Nothing here is jurisdiction-specific. |
| Note | Competitor and market sizing are being researched separately; add findings in §11. |

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
