"""Standalone mcp-chrome micro-service (packaged in the ZIP export).

Exposes the same three tools that the CrewAI GenreScoutAgent uses,
as a plain HTTP JSON API — matching an MCP-tool contract:

    GET  /tools/search_game_refs?genre=platformer
    POST /tools/fetch_gamedev_article  {url}
    GET  /tools/lookup_phaser_docs?topic=physics

Run standalone:
    uvicorn app:app --host 0.0.0.0 --port 8811
"""
from __future__ import annotations

from fastapi import FastAPI, Body, Query
from pydantic import BaseModel

from tools import (
    raw_search_game_refs,
    raw_fetch_gamedev_article,
    raw_lookup_phaser_docs,
)

app = FastAPI(title="mcp-chrome (QuantumForge)")


@app.get("/health")
def health():
    return {"ok": True, "service": "mcp-chrome"}


@app.get("/tools/search_game_refs")
def search(genre: str = Query(...)):
    return {"results": raw_search_game_refs(genre)}


class FetchIn(BaseModel):
    url: str


@app.post("/tools/fetch_gamedev_article")
def fetch(body: FetchIn):
    return {"text": raw_fetch_gamedev_article(body.url)}


@app.get("/tools/lookup_phaser_docs")
def phaser(topic: str = Query(...)):
    return {"doc": raw_lookup_phaser_docs(topic)}
