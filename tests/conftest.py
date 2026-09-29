import os

# Tests never call external LLM providers; the deterministic extractor is used instead.
os.environ["LLM_PROVIDERS"] = ""
