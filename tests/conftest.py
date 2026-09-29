import os

# Tests never call external LLM providers; the deterministic extractor is used instead.
os.environ["LLM_PROVIDERS"] = ""
# The app runs on the in-memory engine in tests; the Neo4j parity test builds its own mirror
# from the Aura credentials in .env (and is skipped when they are absent).
os.environ["STORE"] = "memory"
