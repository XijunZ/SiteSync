# Plaud Demo Recordings (v2: supplier disruption)

**Event (site-specific, not weather):** Apex Roofing's membrane batch for Hackney Wick Yard failed their quality check. The replacement arrives in five working days, so the roof (J1) is **blocked days 225–230**: roof work 220–225, blocked 225–230, resumes 230–235. M&E first fix (K3) can't start until the roof is done (day 235), so Sparks crew S1 has **nothing to do days 230–235**. Those days are lent to Riverside's Bow Wharf; S1 is back on day 235 when K3 can start.

**Constraints (tested):** only the replacement lead time is stated in days ("five working days"); every other time is a weekday. Nobody mentions M&E being affected: SiteSync finds that itself. Press the Plaud **highlight** button at *[highlight]*. Tap **Generate** in the Plaud app if no transcript appears.

## Recording A: Supplier phone call (the input SiteSync pulls; ~50 s)

Plaud Note clipped to the phone (call recording), or two people reading. Sarah (contracts manager, Apex Roofing) calls Dan (site manager).

> **Sarah:** Hi Dan, it's Sarah from Apex Roofing, calling about Hackney Wick Yard.
>
> **Dan:** Hi Sarah, go on.
>
> **Sarah:** Bad news on the membrane. The batch we delivered for your roof failed our quality check this morning, the seams won't bond. We've pulled it. The replacement batch is being made now and it'll be with you in five working days. *[highlight]* So Kev's crew will have to stop on the roof from Thursday until it lands, then they'll finish off. Sorry about this.
>
> **Dan:** Right, understood. Will you keep the same crew?
>
> **Sarah:** Yes, same four lads, they'll come straight back to you when the new batch arrives. Can you extend our booking to cover it?
>
> **Dan:** Yes, I'll sort that on our side. Thanks for letting us know early.

Tested live on Crusoe: 119 words, 1.0 s → J1 +5, reason "membrane batch failed quality check".

## Recording B: On-camera clip (~14 s)

Dan in hi-vis, Plaud clipped on: show device → record → speak → highlight → stop. Cut to laptop.

> *"Morning briefing, Hackney Wick Yard. Apex rang: the roof membrane batch failed their quality check, replacement's due in five working days, so roof waterproofing is on hold until then. Windows and cladding are on track."*

Tested live: 35 words, 1.5 s → J1 +5. Record it once for real beforehand (tap Generate) so its transcript exists; the on-camera take is a re-enactment.

## How it shows up in the demo

1. Dan: **Sync from Plaud** → recordings list → pick the Apex call → transcript with speaker labels and the highlighted line → **Propose update**.
2. SiteSync proposes: *J1 roof waterproofing paused days 225–230 (membrane failed QA), finish 230 → 235*. Knock-on: 18 steps +5, handover 397 → 402, **NEW: Sparks crew 1 idle 230–235** (found by the graph, not mentioned in the call). Neo4j ripple panel shows J1 → J6 → K3 → … → L7.
3. Source line on the change: "Plaud · Apex Roofing call · 16:10" with the quoted sentence. It stays on the event log as evidence.

## Video structure (~7 min)

| Time | Beat | Sponsors shown |
|---|---|---|
| 0:00–0:40 | Problem: one site slips, crews across sites and companies fall out of sync | — |
| 0:40–0:55 | Plaud clip (Recording B) | Plaud |
| 0:55–2:00 | Sync from Plaud → Apex call transcript → J1 paused 225–230 → knock-on (18 steps, 397 → 402, NEW idle S1 230–235) → Neo4j ripple panel → Dan confirms, Priya approves | Plaud, Crusoe, Neo4j |
| 2:00–3:00 | Sync Board: no action +8 vs with action +5; options; Priya offers S1's idle days (anonymised); "How we found this · Neo4j" | Neo4j |
| 3:00–4:15 | Marcus: "M&E crew available near you" → overlay on his timeline → request crew → Priya accepts with return guarantee (day 235) | — |
| 4:15–5:15 | Sam accepts → Marcus confirms → Priya confirms → 3 days protected, £24,000 | — |
| 5:15–5:45 | Neo4j Aura console graph (docs/neo4j-demo.md) | Neo4j |
| 5:45–7:00 | Business model + stack: "Plaud captures, Crusoe understands, Neo4j keeps sites in sync" | All |
