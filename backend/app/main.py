"""FastAPI app: /api/* routes plus the built frontend served from /."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import baseline, candidates, cohort, config, feedback, pipeline, resolver
from .models import (
    BridgeResponse,
    CompareResponse,
    FamiliarityRequest,
    FeedbackRequest,
    FeedbackResponse,
    PlanResponse,
    Profile,
    SessionRequest,
    SessionResponse,
)
from .qloo_adapter import QlooAdapter, QlooError
from .sessions import Session, SessionStore, make_store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("tastebridge")

app = FastAPI(title="TasteBridge", version=config.VERSION)


class _State:
    adapter: QlooAdapter | None = None
    store = make_store()


state = _State()


def get_adapter() -> QlooAdapter:
    if state.adapter is None:
        state.adapter = QlooAdapter()
    return state.adapter


def reset_state() -> None:
    """Used by tests to pick up env changes."""
    state.adapter = None
    state.store = make_store()


class SessionNotFound(Exception):
    pass


async def _session(sid: str) -> Session:
    s = await state.store.get(sid)
    if s is None:
        raise SessionNotFound()
    return s


def _error(status: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, **extra}})


@app.exception_handler(RequestValidationError)
async def _validation(_: Request, exc: RequestValidationError):
    details = []
    for e in exc.errors():
        field = ".".join(str(p) for p in e.get("loc", []) if p != "body")
        details.append(f"{field or 'request'}: {e.get('msg', 'invalid value')}")
    return _error(422, "validation_error", "; ".join(details) or "Invalid request.", details=details)


@app.exception_handler(QlooError)
async def _qloo(_: Request, exc: QlooError):
    log.warning("qloo error %s", exc.code)
    return _error(exc.status, exc.code, exc.user_message)


@app.exception_handler(SessionNotFound)
async def _no_session(_: Request, __: SessionNotFound):
    return _error(404, "session_not_found", "Your session expired or was reset. Please build your bridge again.")


# ---------------- API ----------------


@app.get("/api/health")
async def health():
    adapter = get_adapter()
    return {
        "status": "ok",
        "version": config.VERSION,
        "city": config.CITY["name"],
        "qloo_mode": adapter.mode,
        "qloo_calls_used": adapter.calls_used,
        "qloo_cache_hits": adapter.cache_hits,
        "llm_mode": config.llm_mode(),
        "session_store": "memory" if isinstance(state.store, SessionStore) else "redis",
    }


@app.get("/api/presets")
async def presets():
    return {
        "demo_profile": {
            "origin": "Pakistan",
            "destination_city": config.CITY["name"],
            "preserve": ["food", "music", "friends"],
            "loved_items": [
                {"text": "Coke Studio", "type": "artist"},
                {"text": "Nusrat Fateh Ali Khan", "type": "artist"},
                {"text": "Biryani", "type": "dish"},
                {"text": "Lahore street food", "type": "dish"},
                {"text": "chai with friends", "type": "activity"},
            ],
            "budget_per_activity_cad": 20,
            "hours_per_week": 12,
            "max_travel_minutes": 40,
            "diet": ["none"],
            "comfort": "small_group",
            "familiarity": 0.5,
        },
        "preserve_chips": ["food", "language", "music", "festivals", "friends", "nightlife", "familiarity"],
        "item_types": ["dish", "artist", "show", "place", "activity"],
        "example_items": [
            {"text": "Coke Studio", "type": "artist"},
            {"text": "Biryani", "type": "dish"},
            {"text": "chai with friends", "type": "activity"},
            {"text": "Arijit Singh", "type": "artist"},
            {"text": "Squid Game", "type": "show"},
        ],
        "diets": ["none", "halal", "vegetarian", "vegan", "gluten_free"],
        "comfort_levels": ["solo_ok", "small_group", "prefer_friend"],
        "limits": {"max_loved_items": config.MAX_LOVED_ITEMS, "max_text_len": config.MAX_TEXT_LEN},
    }


@app.post("/api/session", response_model=SessionResponse)
async def create_session(profile: Profile):
    adapter = get_adapter()
    summary = await resolver.resolve(adapter, profile.loved_items)
    cands, notes = await candidates.build_candidates(adapter, profile, summary)
    sid = await state.store.create(Session(profile=profile, resolver=summary, candidates=cands, qloo_notes=notes))
    return SessionResponse(session_id=sid, resolver=summary, qloo_mode=adapter.mode)


@app.delete("/api/session/{session_id}")
async def delete_session(session_id: str):
    return {"deleted": await state.store.delete(session_id)}


@app.post("/api/bridge", response_model=BridgeResponse)
async def bridge(req: SessionRequest):
    s = await _session(req.session_id)
    result = pipeline.bridge(s)
    await state.store.save(req.session_id, s)
    return result


@app.post("/api/plan", response_model=PlanResponse)
async def plan(req: SessionRequest):
    s = await _session(req.session_id)
    result = PlanResponse(plan=await pipeline.make_plan(s), profile=s.profile)
    await state.store.save(req.session_id, s)
    return result


@app.post("/api/feedback", response_model=FeedbackResponse)
async def give_feedback(req: FeedbackRequest):
    s = await _session(req.session_id)
    new_plan, changes, changed_ids = await feedback.handle(s, req.action, req.item_id)
    await state.store.save(req.session_id, s)
    return FeedbackResponse(plan=new_plan, profile=s.profile, changes=changes, changed_ids=changed_ids)


@app.post("/api/familiarity", response_model=BridgeResponse)
async def set_familiarity(req: FamiliarityRequest):
    s = await _session(req.session_id)
    s.profile = s.profile.model_copy(update={"familiarity": req.value})
    s.plan = None  # the next /api/plan call reflects the new slider value
    result = pipeline.bridge(s)
    await state.store.save(req.session_id, s)
    return result


@app.get("/api/compare/{session_id}", response_model=CompareResponse)
async def compare(session_id: str):
    s = await _session(session_id)
    current = s.plan or await pipeline.make_plan(s)
    await state.store.save(session_id, s)
    return CompareResponse(baseline=await baseline.run_baseline(s.profile), tastebridge=current.items, resolver=s.resolver)


@app.get("/api/admin/cohort")
async def admin_cohort():
    return cohort.load_cohort()


@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def api_not_found(path: str):
    return _error(404, "not_found", "Unknown API route.")


# ---------------- Frontend (built by Vite into backend/static) ----------------

if (config.STATIC_DIR / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=config.STATIC_DIR / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        file = (config.STATIC_DIR / path).resolve()
        if path and file.is_file() and config.STATIC_DIR.resolve() in file.parents:
            return FileResponse(file)
        return FileResponse(config.STATIC_DIR / "index.html")
