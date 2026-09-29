from app import ingest
from app.vocab import match_steps, words_to_days
from seed.seed import build_world

def test_words_to_days():
    assert words_to_days("about five days") == 5
    assert words_to_days("a week") == 5
    assert words_to_days("couple of days") == 2
    assert words_to_days("3 days") == 3
    assert words_to_days("all good") is None

def test_match_roof():
    w = build_world()
    assert match_steps(w, "A", "roofing delayed, heavy rain")[0] == "J1"

def test_extract_demo_transcript_offline(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    w = build_world()
    ups = ingest.extract_updates(w, "A", "Roofing delayed, heavy rain, about five days.")
    assert len(ups) == 1 and ups[0].step_code == "J1" and ups[0].delay_days == 5

def test_extract_morning_update_offline(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    w = build_world()
    ups = ingest.extract_updates(w, "A", "Morning update, Site A, Hackney Wick. Heavy rain forecast, so the roof "
                                           "waterproofing is going to be delayed about five days. Scaffold and "
                                           "cladding are on track.")
    assert [(u.step_code, u.delay_days) for u in ups] == [("J1", 5)]

def test_no_update_for_chatter(monkeypatch):
    monkeypatch.setattr(ingest, "_llm_extract", lambda *a, **k: None)
    w = build_world()
    assert ingest.extract_updates(w, "A", "All good today, deliveries arrived.") == []
