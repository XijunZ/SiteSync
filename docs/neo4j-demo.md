# Neo4j in the Demo Video (~20 s)

**Where:** console.neo4j.io → your instance (`sitesync`) → **Query** (or **Explore** → paste as a search query). The graph view draws the result.

**Before filming:** run the demo in the app up to step 4 (J1 confirmed, gap created), so the mirror holds the delayed dates. The query works in any state.

## Query 1: "One delay, two companies, one match" (paste as-is)

```cypher
// The roof delay ripples to M&E first fix, and the same subcontractor
// is already approved at a nearby company that needs M&E right now.
MATCH ripple = (k3:Step {id:'A-K3'})-[:DEPENDS_ON*]->(j1:Step {id:'A-J1'})
MATCH home  = (ng:Org {id:'NG'})-[:RUNS]->(siteA:Site {id:'A'})-[:HAS_STEP]->(k3)
MATCH other = (rv:Org {id:'RV'})-[:RUNS]->(siteC:Site {id:'C'})-[:HAS_STEP]->(ck3:Step {id:'C-K3'})
MATCH idle  = (sparks:Org {id:'SPARKS'})-[:EMPLOYS]->(:Crew)-[:HAS_BOOKING]->(:Booking)-[:FOR_STEP]->(k3)
MATCH need  = (sparks)-[:EMPLOYS]->(:Crew)-[:HAS_BOOKING]->(:Booking)-[:FOR_STEP]->(ck3)
MATCH ok1 = (sparks)-[:APPROVED_AT]->(ng)
MATCH ok2 = (sparks)-[:APPROVED_AT]->(rv)
RETURN ripple, home, other, idle, need, ok1, ok2
```

Returns paths (not loose nodes) so Site and Org nodes are connected. For the distance, run separately: `MATCH (a:Site {id:'A'}),(c:Site {id:'C'}) RETURN round(point.distance(a.loc,c.loc))/1000.0 AS km` → 1.732.

**Captions:** Org → name, Site → name, Step → code, Crew → id, Booking → start. **Layout:** Northgate side left (Site A, J1 → J6 → K3, crew S1), Riverside side right (Site C, C-K3, crew S2), Sparks in the middle bridging both via APPROVED_AT.

**What to say (voiceover):** *"Every project is a graph. The roof delay is a path: roof, weathertight, M&E first fix. The fix is a pattern across companies: the same M&E subcontractor, already approved at Riverside, booked on a site 1.7 km away that needs M&E now. Neo4j finds both in one query."*

**Tip:** in the graph view, give Org, Site, Step, Crew and Booking different colours, and caption Step by `code`, Site by `name`, Org by `name`.

## Query 2 (optional): the whole network at a glance

```cypher
MATCH (o:Org)-[r:RUNS|APPROVED_AT]->(x)
RETURN o, r, x
```

Shows both GCs, their sites, and Sparks/Voltline/CrewNow approvals crossing company lines.

## Query 3 (optional): everything downstream of the roof

```cypher
MATCH p = (d:Step)-[:DEPENDS_ON*]->(:Step {id:'A-J1'})
RETURN p
```
