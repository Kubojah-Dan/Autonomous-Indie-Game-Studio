"""Chrome MCP tools — exposed to CrewAI agents.

Implements a minimal Chrome-MCP-style toolset:
  - search_game_refs(genre)     — DuckDuckGo web search
  - fetch_gamedev_article(url)  — clean article fetch
  - lookup_phaser_docs(topic)   — Phaser 3 documentation lookup

These are usable both as CrewAI @tool functions and as plain callables
that the standalone mcp-chrome service exposes over HTTP.
"""
from __future__ import annotations

import re
from typing import List, Dict

import requests
from bs4 import BeautifulSoup
from crewai.tools import tool


def _ddg_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    """DuckDuckGo HTML search — no API key required."""
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": h.get("title", ""), "url": h.get("href", ""), "snippet": h.get("body", "")}
            for h in hits
        ]
    except Exception as e:
        # Static fallback so the pipeline never breaks
        return [
            {"title": f"[offline] {query}", "url": "", "snippet": f"search unavailable: {e}"}
        ]


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    return "\n".join(lines)[:4000]


def _fetch_article(url: str) -> str:
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 QuantumForge/1.0"})
        r.raise_for_status()
        return _clean_html(r.text)
    except Exception as e:
        return f"[fetch failed: {e}]"


PHASER_TOPICS = {
    "scene": "Phaser.Scene is the primary lifecycle: preload(), create(), update(). Register scenes in the game config.",
    "physics": "Phaser 3 supports Arcade Physics (fast AABB) and Matter.js. Enable via config.physics.default = 'arcade'.",
    "input": "this.input.keyboard.createCursorKeys() for arrows. this.input.on('pointerdown', ...) for mouse.",
    "sprite": "this.add.sprite(x, y, key) or this.physics.add.sprite(). Use setVelocity(), setBounce(), setCollideWorldBounds(true).",
    "graphics": "this.add.graphics().fillStyle(0x00ff41).fillRect(x, y, w, h) — great for prototypes without image assets.",
    "text": "this.add.text(x, y, 'HELLO', { fontSize: '24px', color: '#00ff41', fontFamily: 'monospace' }).",
    "collide": "this.physics.add.collider(objA, objB, callback). Use overlap() for triggers without physical bounce.",
    "group": "this.physics.add.group() to spawn/manage many enemies. group.create(x, y, key).",
    "sound": "this.load.audio('key', 'url') in preload; this.sound.play('key') in create/update.",
    "config": "const config = { type: Phaser.AUTO, width: 800, height: 600, scene: MyScene, physics: {...} }; new Phaser.Game(config);",
}


def _phaser_lookup(topic: str) -> str:
    key = topic.strip().lower()
    for k, v in PHASER_TOPICS.items():
        if k in key or key in k:
            return f"[Phaser::{k}] {v}"
    return (
        "[Phaser::overview] Phaser 3 is a 2D game framework. Load via CDN: "
        "<script src='https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js'></script>. "
        "Available topics: " + ", ".join(PHASER_TOPICS.keys())
    )


# ---------- CrewAI-decorated versions (for Agent tools) ----------

@tool("search_game_refs")
def search_game_refs(genre: str) -> str:
    """Search the web for indie games similar to a given genre or concept.

    Returns a compact list of title/url/snippet triples. Useful for the
    GenreScoutAgent to gather inspiration references.
    """
    hits = _ddg_search(f"best indie {genre} games design inspiration", max_results=5)
    lines = []
    for h in hits:
        lines.append(f"- {h['title']} :: {h['url']}\n  {h['snippet'][:180]}")
    return "\n".join(lines) or "no results"


@tool("fetch_gamedev_article")
def fetch_gamedev_article(url: str) -> str:
    """Fetch and clean the readable text of a game-dev article URL."""
    return _fetch_article(url)


@tool("lookup_phaser_docs")
def lookup_phaser_docs(topic: str) -> str:
    """Return a short Phaser 3 documentation snippet for a topic
    (scene, physics, input, sprite, graphics, text, collide, group, sound, config)."""
    return _phaser_lookup(topic)


# ---------- plain callables (used by the mcp-chrome HTTP service) ----------
def raw_search_game_refs(genre: str) -> List[Dict[str, str]]:
    return _ddg_search(f"best indie {genre} games design inspiration", max_results=5)


def raw_fetch_gamedev_article(url: str) -> str:
    return _fetch_article(url)


def raw_lookup_phaser_docs(topic: str) -> str:
    return _phaser_lookup(topic)
