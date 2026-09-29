import re
import subprocess


class PlaudError(Exception):
    pass


def parse_transcript(raw: str) -> str:
    parts = []
    for line in raw.splitlines():
        line = re.sub(r"^\s*\[\d{1,2}:\d{2}(:\d{2})?\s*-\s*\d{1,2}:\d{2}(:\d{2})?\]\s*", "", line)
        line = re.sub(r"^[^:]{1,30}:\s+", "", line)
        if line.strip():
            parts.append(line.strip())
    return " ".join(parts)


def parse_ids(raw: str) -> list[str]:
    return re.findall(r"\b[0-9a-f]{24,40}\b", raw)


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


def recent_ids() -> list[str]:
    return parse_ids(_run(["recent", "--days", "1"]))


def transcript(file_id: str) -> str:
    try:
        return parse_transcript(_run(["transcript", file_id, "--polished"]))
    except PlaudError:
        return parse_transcript(_run(["transcript", file_id]))
