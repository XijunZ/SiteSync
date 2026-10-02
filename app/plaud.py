import os
import re
import subprocess


class PlaudError(Exception):
    pass


def parse_transcript(raw: str) -> str:
    parts = []
    for line in raw.splitlines():
        if re.match(r"^\s*(- |Transcript:|Summary:)", line):
            continue
        line = re.sub(r"^\s*\[\d{1,2}:\d{2}(:\d{2})?\s*-\s*\d{1,2}:\d{2}(:\d{2})?\]\s*", "", line)
        line = re.sub(r"^[^:]{1,30}:\s+", "", line)
        if line.strip():
            parts.append(line.strip())
    return " ".join(parts)


def parse_ids(raw: str) -> list[str]:
    return re.findall(r"\b(?:of_)?[0-9a-f]{24,40}\b", raw)


def _run(args: list[str]) -> str:
    try:
        r = subprocess.run(["plaud", *args], capture_output=True, text=True, timeout=30)
    except FileNotFoundError as e:
        raise PlaudError("plaud CLI not installed") from e
    except subprocess.TimeoutExpired as e:
        raise PlaudError("Plaud CLI timed out") from e
    if r.returncode == 2:
        raise PlaudError("Plaud login expired: run `plaud login`")
    if r.returncode != 0:
        raise PlaudError(r.stderr.strip() or f"plaud exited {r.returncode}")
    return r.stdout


def parse_recordings(raw: str) -> list[dict]:
    """Parse `plaud recent` rows: `<id>  [title]  <YYYY-MM-DD HH:MM:SS>  <YYYY-MM-DD>  <duration>`."""
    out = []
    for line in raw.splitlines():
        ids = parse_ids(line)
        if not ids:
            continue
        rest = line.replace(ids[0], " ")
        when = re.search(r"\d{4}-\d{2}-\d{2}[ T]\d{1,2}:\d{2}(:\d{2})?", rest)
        dur = re.search(r"\b(\d+h)?\s*(\d+m)?\s*(\d+s)?\s*$", rest.strip())
        duration = dur.group(0).strip() if dur and dur.group(0).strip() else None
        title = rest
        for piece in (when.group(0) if when else None, duration):
            if piece:
                title = title.replace(piece, " ")
        title = re.sub(r"\d{4}-\d{2}-\d{2}", " ", title)
        title = re.sub(r"\s{2,}", " ", title).strip(" |\t") or None
        out.append({"id": ids[0], "title": title, "created_at": when.group(0) if when else None, "duration": duration})
    return out


def parse_speakers(raw: str) -> list[str]:
    seen = []
    for m in re.finditer(r"^\s*(?:\[[^\]]*\]\s*)?([^:\[\]]{1,30}):\s+\S", raw, re.M):
        name = m.group(1).strip()
        if name in ("Transcript", "Summary"):
            continue
        if name and name not in seen:
            seen.append(name)
    return seen


def recordings(limit: int | None = None) -> list[dict]:
    """Recent recordings, newest first. Looks back PLAUD_DAYS days (default 30)."""
    days = os.environ.get("PLAUD_DAYS", "30")
    recs = parse_recordings(_run(["recent", "--days", days]))
    return recs[:limit] if limit else recs


def recent_ids() -> list[str]:
    return [r["id"] for r in recordings()]


def transcript_raw(file_id: str) -> str:
    try:
        return _run(["transcript", file_id, "--polished"])
    except PlaudError:
        return _run(["transcript", file_id])


def transcript(file_id: str) -> str:
    return parse_transcript(transcript_raw(file_id))
