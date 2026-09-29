from pydantic import BaseModel

from app import llm
from app.config import TODAY
from app.domain import World
from app.schedule import forward_pass
from app.vocab import match_steps, words_to_days

CATALOGUE_HORIZON_DAYS = 30


class ExtractedUpdate(BaseModel):
    step_code: str | None
    candidates: list[str] = []
    delay_days: int | None
    reason: str
    excerpt: str
    confidence: float


class ExtractedList(BaseModel):
    updates: list[ExtractedUpdate]


REASONS = ["rain", "weather", "wind", "delivery", "material", "inspection", "labour", "access", "design"]


def _catalogue(world: World, site_id: str, text: str = "") -> str:
    """Only steps a site manager could be talking about: active or starting within the horizon, plus any
    step the note names. Keeps the prompt small, which is what makes extraction fast."""
    dates = forward_pass(world, site_id, "confirmed")
    named = set(match_steps(world, site_id, text)) if text else set()
    keep = [st for st in world.steps.values() if st.site_id == site_id and (
        st.code in named or (dates[st.id][1] > TODAY and dates[st.id][0] < TODAY + CATALOGUE_HORIZON_DAYS))]
    keep.sort(key=lambda st: dates[st.id][0])
    return "\n".join(f"{st.code}: {st.name} ({st.trade})" for st in keep)


def _llm_extract(world: World, site_id: str, text: str) -> list[ExtractedUpdate] | None:
    system = ("You turn construction site voice notes into schedule delay updates. Choose step_code ONLY from the "
              "catalogue. If unsure which step, set step_code null and list candidate codes. Only report work that "
              "is delayed; ignore anything on track. If the note reports no delay, return an empty list. "
              "delay_days is working days (a week = 5). excerpt is the exact phrase from the note.")
    user = f"Catalogue:\n{_catalogue(world, site_id, text)}\n\nVoice note:\n{text}\n\nReturn {{\"updates\": [...]}}"
    try:
        return llm.extract_json(system, user, ExtractedList).updates
    except llm.LLMUnavailable:
        return None


def _deterministic(world: World, site_id: str, text: str) -> list[ExtractedUpdate]:
    days = words_to_days(text)
    steps = match_steps(world, site_id, text)
    t = text.lower()
    if days is None or not steps or not any(w in t for w in ("delay", "late", "behind", "slip")):
        return []
    reason = next((r for r in REASONS if r in t), "unspecified")
    return [ExtractedUpdate(step_code=steps[0], candidates=steps[1:3], delay_days=days, reason=reason,
                            excerpt=text.strip(), confidence=0.6)]


def extract_updates(world: World, site_id: str, text: str) -> list[ExtractedUpdate]:
    codes = {s.code for s in world.steps.values() if s.site_id == site_id}
    got = _llm_extract(world, site_id, text)
    if got is not None:
        out = []
        for u in got:
            if not u.delay_days or u.delay_days <= 0:
                continue
            if u.step_code not in codes:
                u.candidates = [c for c in u.candidates if c in codes]
                u.step_code = None
                if not u.candidates:
                    continue
            out.append(u)
        return out
    return _deterministic(world, site_id, text)
