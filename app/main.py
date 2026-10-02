from pathlib import Path

from fastapi import FastAPI, Header, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app import graph_explain, ingest, llm, plaud, signals, views
from app.graph_neo4j import mirror_sync
from app.network import (decide_cross_proposal, decide_link, decide_view, publish_offer, request_link, request_view,
                         withdraw_offer)
from app.proposals import (StaleProposal, build_proposal, decide_proposal, default_pause_start, edit_to_changes,
                           pause_changes, preview_edit)
from app.sync_engine import approve_option
from seed.seed import build_world

app = FastAPI(title="SiteSync")


def demo_world():
    w = build_world()
    signals.seed_demo_signal(w)
    return w


STATE = {"world": demo_world()}
STATIC = Path(__file__).resolve().parent.parent / "static"


class ApiError(Exception):
    def __init__(self, status: int, error: str, detail: str = ""):
        self.status, self.error, self.detail = status, error, detail


@app.exception_handler(ApiError)
async def api_error(_: Request, e: ApiError):
    return JSONResponse({"error": e.error, "detail": e.detail}, status_code=e.status)


@app.exception_handler(PermissionError)
async def forbidden(_: Request, e: PermissionError):
    return JSONResponse({"error": "forbidden", "detail": str(e)}, status_code=403)


@app.exception_handler(StaleProposal)
async def stale(_: Request, e: StaleProposal):
    return JSONResponse({"error": "stale", "detail": "already decided, or the site changed since"}, status_code=409)


@app.exception_handler(ValueError)
async def invalid(_: Request, e: ValueError):
    return JSONResponse({"error": "invalid", "detail": str(e)}, status_code=400)


def W():
    return STATE["world"]


def user_of(x_user_id: str | None):
    if not x_user_id or x_user_id not in W().users:
        raise ApiError(401, "unknown_user", "send a valid X-User-Id header")
    return W().users[x_user_id]


class TextIn(BaseModel):
    site_id: str
    text: str
    source_label: str | None = None


class PlaudIn(BaseModel):
    site_id: str
    file_id: str | None = None


class DecideIn(BaseModel):
    accept: bool
    pool_terms: dict | None = None


class LinkIn(BaseModel):
    offer_id: str
    purpose: str = "Pool crew capacity"


class OfferIn(BaseModel):
    gap_id: str


class ViewIn(BaseModel):
    anon_id: str


class ShareIn(BaseModel):
    share: bool


class EditIn(BaseModel):
    site_id: str
    step_id: str
    start: int | None = None
    finish: int | None = None
    pause_start: int | None = None
    pause_days: int | None = None
    reason: str | None = None


class ClearIn(BaseModel):
    site_id: str
    step_code: str


class ApproveIn(BaseModel):
    gap_id: str
    mechanism: str


class SignalIn(BaseModel):
    site_id: str
    step_code: str
    days: int
    kind: str = "weather"
    detail: str = "Rain forecast"


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/users")
def users():
    w = W()
    return [{"id": u.id, "name": u.name, "role": u.role,
             "org": w.orgs[u.org_id].name if u.org_id in w.orgs else "SiteSync"} for u in w.users.values()]


@app.get("/api/me")
def me(x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    return {"id": u.id, "name": u.name, "role": u.role,
            "org": W().orgs[u.org_id].name if u.org_id in W().orgs else "SiteSync",
            "sites": views.visible_sites(W(), u)}


@app.get("/api/sites")
def sites(x_user_id: str | None = Header(None)):
    return views.sites_view(W(), user_of(x_user_id))


@app.get("/api/sites/{site_id}/timeline")
def timeline(site_id: str, x_user_id: str | None = Header(None)):
    return views.timeline_view(W(), user_of(x_user_id), site_id)


@app.get("/api/sites/{site_id}/labour")
def labour(site_id: str, x_user_id: str | None = Header(None)):
    return views.labour_view(W(), user_of(x_user_id), site_id)


def _propose_from_text(u, site_id: str, text: str, source_kind: str, extra: dict | None = None) -> dict:
    views.check_site(W(), u, site_id)
    ups = ingest.extract_updates(W(), site_id, text)
    if not ups:
        return {"proposals": [], "candidates": [], "message": "No schedule change found in this note.", "text": text}
    props, candidates = [], []
    for up in ups:
        if not up.step_code:
            candidates.append(up.model_dump())
            continue
        step_id = f"{site_id}-{up.step_code}"
        changes = pause_changes(W(), site_id, step_id, default_pause_start(W(), site_id, step_id),
                                up.delay_days, up.reason)
        props.append(build_proposal(W(), u, site_id, changes,
                                    {"kind": source_kind, "excerpt": up.excerpt, "reason": up.reason,
                                     "confidence": up.confidence, **(extra or {})}))
    return {"proposals": props, "candidates": candidates, "text": text}


@app.post("/api/ingest/text")
def ingest_text(body: TextIn, x_user_id: str | None = Header(None)):
    if body.source_label:
        return _propose_from_text(user_of(x_user_id), body.site_id, body.text, "voice",
                                  {"source_label": body.source_label})
    return _propose_from_text(user_of(x_user_id), body.site_id, body.text, "typed")


@app.get("/api/plaud/recordings")
def plaud_recordings(x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    try:
        return {"recordings": plaud.recordings(limit=1)}
    except plaud.PlaudError as e:
        raise ApiError(502, "plaud", str(e))


@app.get("/api/plaud/recordings/{file_id}/transcript")
def plaud_transcript(file_id: str, x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    try:
        raw = plaud.transcript_raw(file_id)
    except plaud.PlaudError as e:
        raise ApiError(502, "plaud", str(e))
    return {"id": file_id, "text": plaud.parse_transcript(raw), "speakers": plaud.parse_speakers(raw), "raw": raw}


@app.post("/api/ingest/plaud")
def ingest_plaud(body: PlaudIn, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    try:
        fid = body.file_id or (plaud.recent_ids() or [None])[0]
        if not fid:
            raise ApiError(404, "no_recording", "No Plaud recording today (did you tap Generate in the app?)")
        text = plaud.transcript(fid)
    except plaud.PlaudError as e:
        raise ApiError(502, "plaud", str(e))
    return _propose_from_text(u, body.site_id, text, "voice", {"plaud_file_id": fid})


@app.post("/api/proposals/preview")
def proposal_preview(body: EditIn, x_user_id: str | None = Header(None)):
    return preview_edit(W(), user_of(x_user_id), body.site_id, body.step_id, body.start, body.finish,
                        body.pause_start, body.pause_days)


@app.post("/api/proposals")
def proposal_create(body: EditIn, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    views.check_site(W(), u, body.site_id)
    changes = edit_to_changes(W(), body.site_id, body.step_id, body.start, body.finish, body.pause_start,
                              body.pause_days, body.reason)
    return build_proposal(W(), u, body.site_id, changes, {"kind": "timeline", "reason": body.reason or "update",
                                                         "excerpt": None})


@app.get("/api/proposals")
def proposals(site_id: str, x_user_id: str | None = Header(None)):
    return views.proposals_view(W(), user_of(x_user_id), site_id)


@app.post("/api/proposals/{pid}/decide")
def decide(pid: str, body: DecideIn, x_user_id: str | None = Header(None)):
    if pid not in W().proposals:
        raise ApiError(404, "not_found", pid)
    res = decide_proposal(W(), user_of(x_user_id), pid, body.accept)
    if res.get("status") == "APPLIED":
        mirror_sync(W())
    return res


@app.post("/api/signals")
def signal(body: SignalIn, x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    return signals.raise_risk(W(), body.site_id, body.step_code, body.days, body.kind, body.detail)


@app.post("/api/signals/clear")
def signal_clear(body: ClearIn, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    views.check_site(W(), u, body.site_id)
    return signals.clear_risk(W(), body.site_id, body.step_code, u.id)


@app.post("/api/signals/weather/refresh")
def weather(x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    return signals.refresh_weather(W())


@app.get("/api/sync-board")
def sync_board(x_user_id: str | None = Header(None)):
    return views.sync_board_view(W(), user_of(x_user_id))


@app.post("/api/options/approve")
def approve(body: ApproveIn, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    if u.role != "PM":
        raise PermissionError("only a PM can approve options")
    return approve_option(W(), u, body.gap_id, body.mechanism)


@app.get("/api/city")
def city(x_user_id: str | None = Header(None)):
    return views.city_view(W(), user_of(x_user_id))


@app.get("/api/sites/{site_id}/trades")
def site_trades(site_id: str, x_user_id: str | None = Header(None)):
    return views.trades_view(W(), user_of(x_user_id), site_id)


@app.get("/api/city/{anon}/overlay")
def city_overlay(anon: str, x_user_id: str | None = Header(None)):
    return views.overlay_view(W(), user_of(x_user_id), anon)


@app.post("/api/offers")
def offer_publish(body: OfferIn, x_user_id: str | None = Header(None)):
    o = publish_offer(W(), user_of(x_user_id), body.gap_id)
    return {"id": o.id, "status": o.status}


@app.post("/api/needs")
def need_post(body: OfferIn, x_user_id: str | None = Header(None)):
    from app.network import post_need
    nd = post_need(W(), user_of(x_user_id), body.gap_id)
    return {"id": nd.id, "status": nd.status, "workers": nd.workers, "start": nd.start, "end": nd.end}


@app.get("/api/needs")
def needs(x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    return [{"id": n.id, "status": n.status, "trade": n.trade, "workers": n.workers, "start": n.start, "end": n.end,
             "step_id": n.step_id, "offer_id": n.offer_id} for n in W().needs.values() if n.org_id == u.org_id]


@app.get("/api/offers")
def offers(x_user_id: str | None = Header(None)):
    return views.offers_view(W(), user_of(x_user_id))


@app.post("/api/offers/{offer_id}/withdraw")
def offer_withdraw(offer_id: str, x_user_id: str | None = Header(None)):
    o = withdraw_offer(W(), user_of(x_user_id), offer_id)
    return {"id": o.id, "status": o.status}


@app.post("/api/view-requests")
def view_request(body: ViewIn, x_user_id: str | None = Header(None)):
    g = request_view(W(), user_of(x_user_id), body.anon_id)
    return {"id": g.id, "status": g.status}


@app.post("/api/view-requests/{view_id}/decide")
def view_decide(view_id: str, body: ShareIn, x_user_id: str | None = Header(None)):
    g = decide_view(W(), user_of(x_user_id), view_id, body.share)
    return {"id": g.id, "status": g.status}


@app.post("/api/links")
def link_request(body: LinkIn, x_user_id: str | None = Header(None)):
    link = request_link(W(), user_of(x_user_id), body.offer_id, body.purpose)
    return {"id": link.id, "status": link.status}


@app.post("/api/links/{link_id}/decide")
def link_decide(link_id: str, body: DecideIn, x_user_id: str | None = Header(None)):
    link = decide_link(W(), user_of(x_user_id), link_id, body.accept, body.pool_terms)
    return {"id": link.id, "status": link.status, "pool": link.pool}


@app.get("/api/links")
def links(x_user_id: str | None = Header(None)):
    return views.links_view(W(), user_of(x_user_id))


@app.get("/api/cross-proposals")
def cross(x_user_id: str | None = Header(None)):
    return views.cross_proposals_view(W(), user_of(x_user_id))


@app.post("/api/cross-proposals/{cp_id}/decide")
def cross_decide(cp_id: str, body: DecideIn, x_user_id: str | None = Header(None)):
    return decide_cross_proposal(W(), user_of(x_user_id), cp_id, body.accept)


@app.get("/api/requests")
def requests(x_user_id: str | None = Header(None)):
    return views.requests_view(W(), user_of(x_user_id))


@app.get("/api/notifications")
def notifications(x_user_id: str | None = Header(None)):
    return views.notifications_view(W(), user_of(x_user_id))


@app.post("/api/notifications/read")
def notifications_read(x_user_id: str | None = Header(None)):
    return views.mark_read(W(), user_of(x_user_id))


@app.get("/api/sub/bookings")
def sub_bookings(x_user_id: str | None = Header(None)):
    return views.sub_bookings_view(W(), user_of(x_user_id))


@app.get("/api/report")
def report(x_user_id: str | None = Header(None)):
    return views.report_view(W(), user_of(x_user_id))


@app.get("/api/events")
def events(x_user_id: str | None = Header(None)):
    return views.events_view(W(), user_of(x_user_id))


@app.get("/api/graph/ripple")
def graph_ripple(site_id: str, step_code: str, x_user_id: str | None = Header(None)):
    views.check_site(W(), user_of(x_user_id), site_id)
    return graph_explain.ripple(W(), site_id, step_code)


@app.get("/api/graph/swap-explain")
def graph_swap_explain(gap_id: str, x_user_id: str | None = Header(None)):
    u = user_of(x_user_id)
    try:
        graph_explain.check_swap_viewer(W(), u, gap_id)
        return graph_explain.swap_explain(W(), u, gap_id)
    except KeyError:
        raise ApiError(404, "not_found", "no open gap with that id")


@app.get("/api/graph/stats")
def graph_stats(x_user_id: str | None = Header(None)):
    user_of(x_user_id)
    return graph_explain.stats(W())


@app.get("/api/graph/log")
def graph_log():
    from app import graph_neo4j
    return {"calls": [{k: v for k, v in c.items() if k != "_t"} for c in graph_neo4j.GRAPH_LOG[-12:][::-1]]}


@app.get("/api/llm/log")
def llm_log():
    return {"calls": llm.CALL_LOG[-50:]}


@app.post("/api/demo/reset")
def reset():
    STATE["world"] = demo_world()
    llm.CALL_LOG.clear()
    synced = mirror_sync(W())
    from app import graph_neo4j
    graph_neo4j.GRAPH_LOG.clear()  # start the demo with an empty activity panel
    return {"ok": True, "neo4j_synced": synced}
