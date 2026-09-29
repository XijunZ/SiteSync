import re

from app.domain import World

SYNONYMS = {
    "J1": ["roof", "roofing", "membrane", "waterproofing"],
    "J2": ["windows lower", "glazing lower"], "J3": ["windows upper", "glazing upper"],
    "J4": ["cladding lower", "brick slip"], "J5": ["cladding upper"],
    "K1": ["blockwork lower", "party walls"], "K3": ["first fix", "m&e first fix", "electrics first fix"],
    "K5": ["risers", "plant room"], "K6": ["first fix inspection"],
    "K8": ["drylining lower", "plastering", "screed"], "H7": ["props", "back-propping"],
}
NUMBERS = {"one": 1, "a": 1, "two": 2, "couple": 2, "three": 3, "four": 4, "five": 5, "six": 6,
           "seven": 7, "eight": 8, "nine": 9, "ten": 10}


def words_to_days(text: str) -> int | None:
    t = text.lower()
    m = re.search(r"(\d+)\s*(working\s+)?days?\b", t)
    if m:
        return int(m.group(1))
    m = re.search(r"\b(a|one|two|couple)\s+(of\s+)?weeks?\b", t)
    if m:
        return 5 * NUMBERS[m.group(1)]
    m = re.search(r"\b(" + "|".join(NUMBERS) + r")\s+(of\s+)?(working\s+)?days?\b", t)
    if m:
        return NUMBERS[m.group(1)]
    return None


def match_steps(world: World, site_id: str, text: str) -> list[str]:
    t = text.lower()
    hits: dict[str, int] = {}
    for code, words in SYNONYMS.items():
        found = [w for w in words if re.search(rf"\b{re.escape(w)}", t)]
        if found:
            hits[code] = max(hits.get(code, 0), max(len(w) for w in found))
    for st in world.steps.values():
        if st.site_id == site_id and st.name.lower() in t:
            hits[st.code] = max(hits.get(st.code, 0), len(st.name))
    return [c for c, _ in sorted(hits.items(), key=lambda kv: -kv[1])]
