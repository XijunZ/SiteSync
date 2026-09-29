import os

import pytest

from app import config  # noqa: F401  (loads .env for the Neo4j credentials)
from app.schedule import forward_pass
from app.sync_engine import open_gaps, swap_candidates_memory, swap_candidates_neo4j
from seed.seed import build_world

pytestmark = pytest.mark.skipif(not os.getenv("NEO4J_URI") or not os.getenv("NEO4J_PASSWORD"),
                                reason="Neo4j not configured")


@pytest.fixture(scope="module")
def mirror():
    from app.graph_neo4j import Neo4jMirror
    try:
        m = Neo4jMirror(os.environ["NEO4J_URI"], os.getenv("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"])
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"Neo4j unreachable: {type(e).__name__}")
    yield m
    m.close()


def test_cypher_propagation_matches_python(mirror):
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    w.steps["C-J1"].risk_days = 2
    w.steps["B-G5"].lag_days = 3  # timeline start shift (spec v2.1)
    mirror.sync(w)
    for site in w.sites:
        for mode in ("baseline", "confirmed", "risk"):
            assert mirror.propagate(site, mode) == forward_pass(w, site, mode), (site, mode)


def test_cypher_swap_search_matches_memory(mirror):
    w = build_world()
    w.steps["A-J1"].delay_days = 5
    mirror.sync(w)
    gap = open_gaps(w)[0]
    cypher = swap_candidates_neo4j(w, gap, mirror)
    memory = swap_candidates_memory(w, gap)
    assert [(s, c) for s, c, _ in cypher] == [(s, c) for s, c, _ in memory]
    assert cypher[0][0] == "C-K3" and round(cypher[0][2], 1) == 1.7
