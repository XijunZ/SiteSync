import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

TODAY = 220
LOOKAHEAD_DAYS = 20
RETURN_LAG_DAYS = 3
CREW_DAY_GBP = 1200
MAX_SWAP_KM = 10.0
PM_CRITICAL_SLIP_DAYS = 2
STORE = os.getenv("STORE", "memory")
LLM_PROVIDERS = [p.strip() for p in os.getenv("LLM_PROVIDERS", "crusoe").split(",") if p.strip()]
