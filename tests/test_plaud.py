from app.plaud import parse_ids, parse_transcript

def test_parse_transcript_strips_timestamps_and_speakers():
    raw = "[00:00 - 00:04] Speaker 1: Roofing delayed,\n[00:04 - 00:09] Speaker 1: heavy rain, about five days."
    assert parse_transcript(raw) == "Roofing delayed, heavy rain, about five days."

def test_parse_ids_finds_hex_ids():
    raw = "ID                                Name\n0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b  Site A 07:42\n"
    assert parse_ids(raw) == ["0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b"]


def test_recordings_looks_back_and_keeps_only_latest(monkeypatch):
    import app.plaud as plaud
    calls = []
    out = ("  of_b5b56ddd0dacb52c8c38f35511443704  Site Update: Hackney Wick Yard  2026-09-29  1m02s\n"
           "  of_760c48c8bc548b2d33f68dadd8256585  2026-09-29 15:03:43  2026-09-29  5s\n")
    monkeypatch.setattr(plaud, "_run", lambda args: calls.append(args) or out)
    monkeypatch.delenv("PLAUD_DAYS", raising=False)
    recs = plaud.recordings(limit=1)
    assert calls[0] == ["recent", "--days", "30"]
    assert [r["id"] for r in recs] == ["of_b5b56ddd0dacb52c8c38f35511443704"]
    monkeypatch.setenv("PLAUD_DAYS", "7")
    plaud.recordings()
    assert calls[1] == ["recent", "--days", "7"]
