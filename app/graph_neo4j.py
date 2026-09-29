"""Neo4j Aura mirror of the world: graph-native propagation and slot-swap search.

The in-memory World stays the engine's working state; this mirror is rebuilt from it (≈1k nodes) and
answers the graph questions in Cypher. Parity with the Python engine is asserted in tests.
"""
import logging
import os

from neo4j import GraphDatabase

from app import config
from app.domain import World


SWAP_CYPHER = """MATCH (home:Site {id:$home}), (sub:Org {id:$sub})-[:EMPLOYS]->(c:Crew)-[:HAS_BOOKING]->(b:Booking)
                     -[:FOR_STEP]->(st:Step {trade:$trade})<-[:HAS_STEP]-(t:Site)<-[:RUNS]-(gc:Org)
               WHERE t.id <> home.id AND EXISTS { (sub)-[:APPROVED_AT]->(gc) }
               WITH t, st, c, gc, b, point.distance(home.loc, t.loc) / 1000.0 AS km
               WHERE km <= $max_km
               RETURN t.id AS site_id, st.id AS step_id, c.id AS crew_id, gc.id AS gc_id, km,
                      b.start AS start, b.end AS end
               ORDER BY km, step_id"""

# Driving chain: each hop is a dependency that actually sets the next step's start (confirmed dates on the nodes).
RIPPLE_CYPHER = """MATCH p = (done:Step {id:$end})-[:DEPENDS_ON*]->(s:Step {id:$start})
WHERE all(r IN relationships(p) WHERE startNode(r).conf_start = endNode(r).conf_end)
RETURN [n IN reverse(nodes(p)) | n {.code, .name, .conf_start, .conf_end}] AS path, length(p) AS hops
ORDER BY hops DESC LIMIT 1"""

RIPPLE_FALLBACK_CYPHER = """MATCH p = (done:Step {id:$end})-[:DEPENDS_ON*]->(s:Step {id:$start})
RETURN [n IN reverse(nodes(p)) | n {.code, .name, .conf_start, .conf_end}] AS path, length(p) AS hops
ORDER BY hops DESC LIMIT 1"""

AFFECTED_CYPHER = """MATCH (s:Step {id:$start})<-[:DEPENDS_ON*]-(d:Step)
RETURN count(DISTINCT d) AS n"""

_MIRROR = None
_MIRROR_FAILED = False


class Neo4jMirror:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.driver.verify_connectivity()

    def close(self) -> None:
        self.driver.close()

    def sync(self, world: World) -> None:
        orgs = [{"id": o.id, "name": o.name, "type": o.type} for o in world.orgs.values()]
        sites = [{"id": s.id, "name": s.name, "org_id": s.org_id, "lat": s.lat, "lon": s.lon, "offset": s.offset}
                 for s in world.sites.values()]
        from app.schedule import all_dates
        conf = all_dates(world, "confirmed")
        steps = [{"id": s.id, "site_id": s.site_id, "code": s.code, "name": s.name, "trade": s.trade, "days": s.days,
                  "delay": s.delay_days, "risk": s.risk_days, "lag": s.lag_days, "pause": s.pause_start, "deps": s.deps,
                  "cs": conf[s.site_id][s.id][0], "ce": conf[s.site_id][s.id][1]} for s in world.steps.values()]
        crews = [{"id": c.id, "org_id": c.org_id, "trade": c.trade} for c in world.crews.values()]
        bookings = [{"id": b.id, "crew_id": b.crew_id, "step_id": b.step_id, "start": b.start, "end": b.end}
                    for b in world.bookings.values()]
        approvals = [{"sub": a.sub_org_id, "gc": a.gc_org_id, "setup": a.setup_days} for a in world.approvals]

        def work(tx):
            tx.run("MATCH (n) DETACH DELETE n")
            tx.run("UNWIND $rows AS r CREATE (:Org {id:r.id, name:r.name, type:r.type})", rows=orgs)
            tx.run("""UNWIND $rows AS r MATCH (o:Org {id:r.org_id})
                      CREATE (o)-[:RUNS]->(:Site {id:r.id, name:r.name, offset:r.offset,
                              loc: point({latitude:r.lat, longitude:r.lon})})""", rows=sites)
            tx.run("""UNWIND $rows AS r MATCH (si:Site {id:r.site_id})
                      CREATE (si)-[:HAS_STEP]->(:Step {id:r.id, site_id:r.site_id, code:r.code, name:r.name, trade:r.trade,
                              days:r.days, delay:r.delay, risk:r.risk, lag:r.lag, pause_start:r.pause,
                              conf_start:r.cs, conf_end:r.ce})""", rows=steps)
            tx.run("""UNWIND $rows AS r UNWIND r.deps AS d MATCH (a:Step {id:r.id}), (b:Step {id:d})
                      CREATE (a)-[:DEPENDS_ON]->(b)""", rows=steps)
            tx.run("""UNWIND $rows AS r MATCH (o:Org {id:r.org_id})
                      CREATE (o)-[:EMPLOYS]->(:Crew {id:r.id, trade:r.trade})""", rows=crews)
            tx.run("""UNWIND $rows AS r MATCH (c:Crew {id:r.crew_id}), (st:Step {id:r.step_id})
                      CREATE (c)-[:HAS_BOOKING]->(:Booking {id:r.id, start:r.start, end:r.end})-[:FOR_STEP]->(st)""",
                   rows=bookings)
            tx.run("""UNWIND $rows AS r MATCH (a:Org {id:r.sub}), (g:Org {id:r.gc})
                      CREATE (a)-[:APPROVED_AT {setup_days:r.setup}]->(g)""", rows=approvals)

        with self.driver.session() as s:
            s.execute_write(work)

    def propagate(self, site_id: str, mode: str = "confirmed") -> dict[str, tuple[int, int]]:
        extra = {"baseline": "0", "confirmed": "s.delay", "risk": "s.delay + s.risk"}[mode]
        lag = "0" if mode == "baseline" else "s.lag"

        def work(tx):
            tx.run(f"""MATCH (si:Site {{id:$site}})-[:HAS_STEP]->(s:Step)
                       SET s.p_start = si.offset + {lag}, s.p_end = si.offset + {lag} + s.days + {extra}""", site=site_id)
            for _ in range(60):
                shifted = tx.run(f"""MATCH (s:Step {{site_id:$site}})-[:DEPENDS_ON]->(d:Step)
                                     WITH s, max(d.p_end) AS ready
                                     WHERE ready + {lag} > s.p_start
                                     SET s.p_start = ready + {lag}, s.p_end = ready + {lag} + s.days + {extra}
                                     RETURN count(s) AS n""", site=site_id).single()["n"]
                if shifted == 0:
                    break
            return {r["id"]: (r["a"], r["b"]) for r in tx.run(
                "MATCH (s:Step {site_id:$site}) RETURN s.id AS id, s.p_start AS a, s.p_end AS b", site=site_id)}

        with self.driver.session() as s:
            return s.execute_write(work)

    def swap_candidates(self, sub_org_id: str, home_site_id: str, trade: str, max_km: float) -> list[dict]:
        with self.driver.session() as s:
            return [dict(r) for r in s.run(SWAP_CYPHER, home=home_site_id, sub=sub_org_id, trade=trade, max_km=max_km)]

    def ripple(self, start_id: str, end_id: str) -> dict:
        """Driving chain from a step to handover, plus everything downstream of it."""
        with self.driver.session() as s:
            row = s.run(RIPPLE_CYPHER, start=start_id, end=end_id).single()
            if row is None:
                row = s.run(RIPPLE_FALLBACK_CYPHER, start=start_id, end=end_id).single()
            affected = s.run(AFFECTED_CYPHER, start=start_id).single()["n"]
        return {"path": row["path"] if row else [], "hops": row["hops"] if row else 0, "affected_count": affected}

    def stats(self) -> dict:
        with self.driver.session() as s:
            n = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
            r = s.run("MATCH ()-[r]->() RETURN count(r) AS n").single()["n"]
        return {"nodes": n, "relationships": r}


def get_mirror() -> "Neo4jMirror | None":
    """Lazy singleton; None unless STORE=neo4j and Aura is reachable. Never raises."""
    global _MIRROR, _MIRROR_FAILED
    if config.STORE != "neo4j" or _MIRROR_FAILED:
        return None
    if _MIRROR is None:
        try:
            _MIRROR = Neo4jMirror(os.environ["NEO4J_URI"], os.getenv("NEO4J_USER", "neo4j"),
                                  os.environ["NEO4J_PASSWORD"])
        except Exception as e:  # noqa: BLE001 - Neo4j is optional; the in-memory engine still works
            logging.warning("Neo4j mirror unavailable: %s", type(e).__name__)
            _MIRROR_FAILED = True
            return None
    return _MIRROR


def mirror_sync(world: World) -> bool:
    m = get_mirror()
    if not m:
        return False
    try:
        m.sync(world)
        return True
    except Exception as e:  # noqa: BLE001 - best effort; never break a request
        logging.warning("Neo4j sync failed: %s", type(e).__name__)
        return False
