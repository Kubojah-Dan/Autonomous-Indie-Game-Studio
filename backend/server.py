"""QuantumForge AI — FastAPI backend.

Routes:
    POST /api/forge/new                  {idea} -> {game_id}
    WS   /api/agents/stream/{game_id}    live pipeline events
    GET  /api/vault                      list all forged games
    GET  /api/game/{game_id}             metadata
    GET  /api/game/{game_id}/play        serve playable HTML
    GET  /api/game/{game_id}/download    serve zip
    GET  /api/mcp/search?genre=...       chrome-MCP: search_game_refs
    GET  /api/mcp/phaser?topic=...       chrome-MCP: lookup_phaser_docs
    POST /api/mcp/fetch                  chrome-MCP: fetch_gamedev_article
    GET  /api/health
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from fastapi.responses import HTMLResponse, Response
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from starlette.middleware.cors import CORSMiddleware

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

from forge.crew import ForgePipeline
from forge.game_writer import write_game, build_zip, GENERATED_DIR
from forge.demo import DEMO_ID, DEMO_IDEA, demo_artifacts
from forge.tools import raw_search_game_refs, raw_fetch_gamedev_article, raw_lookup_phaser_docs

# --- logging ---
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s :: %(message)s")
log = logging.getLogger("quantumforge")

# --- mongo ---
mongo_url = os.environ["MONGO_URL"]
db_name = os.environ["DB_NAME"]
mongo = AsyncIOMotorClient(mongo_url)
db = mongo[db_name]

# --- app ---
app = FastAPI(title="QuantumForge AI")
api = APIRouter(prefix="/api")

# Per-job event queues (game_id -> asyncio.Queue)
JOB_QUEUES: Dict[str, asyncio.Queue] = {}
JOB_HISTORY: Dict[str, list] = {}  # replay buffer for reconnecting clients


class ForgeIn(BaseModel):
    idea: str = Field(..., min_length=3, max_length=280)


class GameMeta(BaseModel):
    id: str
    idea: str
    created_at: str
    status: str
    cover_seed: int = 0


def _cover_seed(idea: str) -> int:
    return sum(ord(c) for c in idea) % 360


async def _seed_demo():
    existing = await db.games.find_one({"_id": DEMO_ID})
    if existing:
        return
    write_game(DEMO_ID, DEMO_IDEA, demo_artifacts())
    await db.games.insert_one({
        "_id": DEMO_ID,
        "idea": DEMO_IDEA,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "done",
        "artifacts": demo_artifacts(),
        "cover_seed": _cover_seed(DEMO_IDEA),
        "demo": True,
    })
    log.info("seeded demo game '%s'", DEMO_ID)


@app.on_event("startup")
async def _startup():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    await _seed_demo()


@app.on_event("shutdown")
async def _shutdown():
    mongo.close()


# ------------------ health ------------------
@api.get("/health")
async def health():
    return {"ok": True, "service": "quantumforge", "generated_dir": str(GENERATED_DIR)}


# ------------------ MCP tool endpoints ------------------
@api.get("/mcp/search")
async def mcp_search(genre: str = Query(..., min_length=1)):
    return {"tool": "search_game_refs", "results": raw_search_game_refs(genre)}


@api.get("/mcp/phaser")
async def mcp_phaser(topic: str = Query(...)):
    return {"tool": "lookup_phaser_docs", "topic": topic, "doc": raw_lookup_phaser_docs(topic)}


@api.post("/mcp/fetch")
async def mcp_fetch(payload: dict = Body(...)):
    url = payload.get("url", "")
    if not url:
        raise HTTPException(400, "url required")
    return {"tool": "fetch_gamedev_article", "url": url, "text": raw_fetch_gamedev_article(url)}


# ------------------ forge pipeline ------------------
def _emit_factory(queue: asyncio.Queue, loop: asyncio.AbstractEventLoop, history: list):
    """Return a thread-safe emit fn used by the sync pipeline runner."""
    def emit(event: Dict[str, Any]):
        event = {**event, "ts": datetime.now(timezone.utc).isoformat()}
        history.append(event)
        asyncio.run_coroutine_threadsafe(queue.put(event), loop)
    return emit


async def _run_pipeline(game_id: str, idea: str):
    queue = JOB_QUEUES[game_id]
    history = JOB_HISTORY[game_id]
    loop = asyncio.get_running_loop()
    emit = _emit_factory(queue, loop, history)

    def sync_runner():
        pipeline = ForgePipeline(idea, emit)
        return pipeline.run()

    try:
        artifacts = await asyncio.to_thread(sync_runner)
        write_game(game_id, idea, artifacts)
        await db.games.update_one(
            {"_id": game_id},
            {"$set": {"status": "done", "artifacts": artifacts,
                      "finished_at": datetime.now(timezone.utc).isoformat()}},
        )
        emit({"type": "done", "game_id": game_id})
    except Exception as e:
        log.exception("pipeline failed")
        await db.games.update_one({"_id": game_id}, {"$set": {"status": "error", "error": str(e)}})
        emit({"type": "error", "error": str(e)})


@api.post("/forge/new")
async def forge_new(payload: ForgeIn):
    game_id = uuid.uuid4().hex[:12]
    JOB_QUEUES[game_id] = asyncio.Queue()
    JOB_HISTORY[game_id] = []
    doc = {
        "_id": game_id,
        "idea": payload.idea,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "running",
        "artifacts": {},
        "cover_seed": _cover_seed(payload.idea),
    }
    await db.games.insert_one(doc)
    asyncio.create_task(_run_pipeline(game_id, payload.idea))
    return {"game_id": game_id, "stream_url": f"/api/agents/stream/{game_id}"}


@app.websocket("/api/agents/stream/{game_id}")
async def stream(ws: WebSocket, game_id: str):
    await ws.accept()
    q = JOB_QUEUES.get(game_id)
    history = JOB_HISTORY.get(game_id, [])
    if q is None:
        # Job unknown or already flushed — replay from DB
        doc = await db.games.find_one({"_id": game_id})
        if doc and doc.get("status") == "done":
            await ws.send_text(json.dumps({"type": "done", "game_id": game_id, "replay": True}))
        else:
            await ws.send_text(json.dumps({"type": "error", "error": "unknown game_id"}))
        await ws.close()
        return

    try:
        # replay buffered history first
        for e in list(history):
            await ws.send_text(json.dumps(e))
            if e.get("type") in {"done", "error"}:
                await ws.close(); return
        while True:
            event = await q.get()
            await ws.send_text(json.dumps(event))
            if event.get("type") in {"done", "error"}:
                break
    except WebSocketDisconnect:
        return
    finally:
        try:
            await ws.close()
        except Exception:
            pass


# ------------------ vault ------------------
@api.get("/vault")
async def vault():
    cursor = db.games.find({}, {"artifacts": 0}).sort("created_at", -1)
    items = []
    async for doc in cursor:
        items.append({
            "id": doc["_id"],
            "idea": doc.get("idea", ""),
            "status": doc.get("status", "unknown"),
            "created_at": doc.get("created_at", ""),
            "cover_seed": doc.get("cover_seed", 0),
            "demo": bool(doc.get("demo", False)),
        })
    return {"games": items}


@api.get("/game/{game_id}")
async def game_meta(game_id: str):
    doc = await db.games.find_one({"_id": game_id})
    if not doc:
        raise HTTPException(404, "game not found")
    doc["id"] = doc.pop("_id")
    return doc


@api.get("/game/{game_id}/play", response_class=HTMLResponse)
async def play(game_id: str):
    p = GENERATED_DIR / game_id / "index.html"
    if not p.exists():
        raise HTTPException(404, "not built yet")
    return HTMLResponse(p.read_text(encoding="utf-8"))


@api.get("/game/{game_id}/download")
async def download(game_id: str):
    p = GENERATED_DIR / game_id
    if not p.exists():
        raise HTTPException(404, "not built yet")
    data = build_zip(game_id)
    return Response(
        content=data,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{game_id}.zip"'},
    )


app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
