# Plaud Demo Recordings

Two real-world captures for the Plaud integration. Record each 2–3 times on the Plaud device; keep the cleanest.

**Constraints built in (don't change without re-testing extraction):**
- Only the roof delay is stated as a number of days ("five working days"). Every other time reference is a weekday or date.
- Nobody says M&E is affected. SiteSync must work that out from the dependency graph (the demo's key moment).
- Press the Plaud **highlight** button at the lines marked *[press highlight]*.
- If no transcript appears automatically, tap **Generate** in the Plaud app.

## Recording 1: Start-of-shift briefing (~2.5 min, 3–4 voices)

07:30, Site A (Hackney Wick Yard), welfare cabin. Dan (site manager), Kev (roofing foreman, Apex Roofing), Mo (cladding foreman), Jess (glazing).

> **Dan:** Morning all, it's Tuesday, Hackney Wick Yard. Quick one because the weather's turning. Headcount first: we've got twenty-two on site today, roofers four, glaziers four, cladding five, plus the frame lads striking props on level five. Safety point for today: wind's picking up this afternoon, so no loose sheet materials on the roof after lunch, everything strapped or brought down.
>
> **Dan:** Kev, roof. Where are we?
>
> **Kev:** Membrane's started on the north side, about fifteen percent down. Problem is the forecast. Heavy rain Thursday into the weekend, and it's not stopping by the look of it. We can't lay single-ply in the wet, the adhesive won't take and the warranty's void if we try. Realistically the roof waterproofing is going to be delayed about five working days. We'll keep going today and tomorrow while it's dry.
>
> **Dan:** *[press highlight]* Right. So roof finishes a week later than planned, and the building's not watertight until then. I'll put that in and let Priya know. Anything we can do to claw it back?
>
> **Kev:** We could tent the north side but it's not worth it for membrane, honestly. Better to just go hard when it clears.
>
> **Dan:** Okay. Jess, windows?
>
> **Jess:** Upper floors are on track. Frames for level four arrived yesterday, we'll be glazing level four through to Friday. No issues.
>
> **Dan:** Good. Mo, cladding?
>
> **Mo:** Lower floors on track. Brick-slip panels for the east elevation land Wednesday morning, I need the hoist from eight till ten.
>
> **Dan:** Fine, hoist is yours eight till ten Wednesday. Scaffold was inspected yesterday, tags are all green. Last thing, the electricians from Sparks are booked to start first fix on the lower floors on the eighth. I'll check with Priya that still works. Right, that's it. Stay dry, strap everything down this afternoon.

## Recording 2: Supplier phone call (~1 min; Plaud Note clipped to the phone)

16:10 the same day. Sarah (contracts manager, Apex Roofing) calls Dan.

> **Sarah:** Hi Dan, it's Sarah from Apex Roofing, calling about Hackney Wick Yard.
>
> **Dan:** Hi Sarah, go on.
>
> **Sarah:** Just to confirm what Kev said this morning. We've looked at the Met Office outlook, it's heavy rain from Thursday through to next Tuesday. Single-ply can't go down in that, so we're standing the membrane crew down from Thursday. We'll pick up again on the Wednesday after, weather permitting. So the roof waterproofing will be delayed by five working days. *[press highlight]*
>
> **Dan:** Understood. Will you keep the same crew?
>
> **Sarah:** Yes, same four, they'll come straight back to you. Can you extend our booking to cover it? I'll send the revised dates over email.
>
> **Dan:** Yes, I'll extend it on our side. Thanks for the heads-up.

## Version B: on-camera clip (~12 s)

Dan in hi-vis, Plaud clipped on: show device → record → speak → press highlight → stop. Cut to laptop: "Sync from Plaud" → transcript → J1 +5.

> *"Morning briefing, Hackney Wick Yard. Kev says heavy rain from Thursday, so the roof waterproofing is delayed about five working days. Windows and cladding are on track."*

Tested: 27 words (~11 s spoken); live Crusoe 0.9–1.4 s → J1 +5; offline fallback → J1 +5.

**Before filming:** record Version B once for real (tap Generate) so the transcript already exists; the on-camera take is a re-enactment and the app pulls the pre-recorded one. Also record Recordings 1 and 2 above to show as the full multi-speaker briefing and the supplier call.

## Video structure (7 min)

| Time | Beat | Sponsors shown |
|---|---|---|
| 0:00–0:40 | Problem: one site slips, crews across sites/companies fall out of sync | — |
| 0:40–0:55 | Plaud clip (Version B) | Plaud |
| 0:55–2:00 | Sync from Plaud → J1 +5 → knock-on (18 steps, 397 → 402, Sparks idle 230–235 found by itself) → Dan confirms, Priya approves | Plaud, Crusoe, Neo4j |
| 2:00–3:15 | Sync Board: no action +8 vs with action +5; ranked options with deadlines; M1 infeasible with reason | Neo4j |
| 3:15–4:30 | City view → request view → trades overlay → request link → Marcus accepts pool | Neo4j (geo) |
| 4:30–5:30 | Slot swap: Sparks accepts → each GC confirms → 3 days protected, £24k | — |
| 5:30–6:15 | Evidence trail (Plaud note, supplier call, snapshots); Brave company check | Plaud, Brave |
| 6:15–7:00 | Business model + stack: "Plaud captures, Crusoe understands, Neo4j keeps sites in sync" | All |

## Expected result in SiteSync

- **Briefing →** exactly one proposed change: A-J1 roof waterproofing +5 working days, reason weather, source = highlighted excerpt with speaker. Headcount, safety, glazing, cladding, hoist and scaffold items produce no change.
- **Knock-on:** 18 steps +5, handover 397 → 402, new gap: Sparks S1 (6) idle days 230–235 on A-K3.
- **Supplier call →** corroborates the same change ("confirmed by Apex Roofing"); supports the assumed booking extension for the roofing crew.
