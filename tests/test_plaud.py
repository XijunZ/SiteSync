from app.plaud import parse_ids, parse_transcript

def test_parse_transcript_strips_timestamps_and_speakers():
    raw = "[00:00 - 00:04] Speaker 1: Roofing delayed,\n[00:04 - 00:09] Speaker 1: heavy rain, about five days."
    assert parse_transcript(raw) == "Roofing delayed, heavy rain, about five days."

def test_parse_ids_finds_hex_ids():
    raw = "ID                                Name\n0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b  Site A 07:42\n"
    assert parse_ids(raw) == ["0f3c9a1b2c3d4e5f6a7b8c9d0e1f2a3b"]
