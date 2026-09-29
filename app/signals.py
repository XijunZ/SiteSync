import httpx

from app.config import TODAY
from app.domain import World
from app.schedule import forward_pass, site_finish


def raise_risk(world: World, site_id: str, step_code: str, days: int, kind: str, detail: str) -> dict:
    st = world.steps.get(f"{site_id}-{step_code}")
    if st is None:
        raise ValueError(f"unknown step {step_code} on site {site_id}")
    st.risk_days = days
    world.log("RiskFlagRaised", None, site_id, {"step_id": st.id, "days": days, "kind": kind, "detail": detail},
              {"kind": "signal", "excerpt": detail})
    return {"site_id": site_id, "step_code": st.code,
            "question": f"{detail}: {st.code} {st.name} at risk of +{days} days. Confirm impact?",
            "risk_finish": site_finish(forward_pass(world, site_id, "risk")),
            "confirmed_finish": site_finish(forward_pass(world, site_id, "confirmed"))}


def clear_risk(world: World, site_id: str, step_code: str) -> None:
    st = world.steps[f"{site_id}-{step_code}"]
    st.risk_days = 0
    world.log("RiskFlagCleared", None, site_id, {"step_id": st.id})


def wet_days(daily_precip_mm: list[float], threshold: float = 2.0) -> list[int]:
    return [i for i, mm in enumerate(daily_precip_mm) if mm is not None and mm >= threshold]


def refresh_weather(world: World) -> list[dict]:
    flags = []
    for site in world.sites.values():
        r = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
            "latitude": site.lat, "longitude": site.lon, "daily": "precipitation_sum", "forecast_days": 7})
        r.raise_for_status()
        wet = wet_days(r.json()["daily"]["precipitation_sum"])
        dates = forward_pass(world, site.id, "confirmed")
        for st in world.steps.values():
            if st.site_id != site.id or not st.weather_sensitive:
                continue
            s, e = dates[st.id]
            hit = [d for d in wet if s <= TODAY + d < e]
            if hit:
                flags.append(raise_risk(world, site.id, st.code, len(hit), "weather",
                                        f"Rain forecast on {len(hit)} day(s)"))
    return flags
