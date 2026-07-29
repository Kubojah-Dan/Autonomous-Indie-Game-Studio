"""Local copy of the same tool helpers used by the main backend, so the
mcp-chrome service is self-contained inside the ZIP."""
from __future__ import annotations

from typing import List, Dict
import requests
from bs4 import BeautifulSoup


def _ddg_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max_results))
        return [
            {"title": h.get("title", ""), "url": h.get("href", ""), "snippet": h.get("body", "")}
            for h in hits
        ]
    except Exception as e:
        return [{"title": f"[offline] {query}", "url": "", "snippet": str(e)}]


def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    return "\n".join(ln.strip() for ln in text.splitlines() if ln.strip())[:4000]


PHASER_TOPICS = {
    "scene":    "Phaser.Scene lifecycle: preload/create/update. Register scenes in game config.",
    "physics":  "Arcade Physics (AABB) or Matter. Enable via config.physics.default='arcade'.",
    "input":    "createCursorKeys() for arrows. this.input.on('pointerdown') for mouse.",
    "sprite":   "this.add.sprite / physics.add.sprite; setVelocity, setBounce, setCollideWorldBounds.",
    "graphics": "add.graphics().fillStyle(0x00ff41).fillRect(x,y,w,h) — great for prototypes.",
    "text":     "add.text(x,y,'HELLO',{fontSize:'24px',color:'#00ff41',fontFamily:'monospace'}).",
    "collide":  "physics.add.collider(a,b,cb). overlap() for triggers without bounce.",
    "group":    "physics.add.group(). group.create(x,y,key). Manage many enemies.",
    "sound":    "load.audio('k',url) in preload; sound.play('k') in create/update.",
    "config":   "new Phaser.Game({type:AUTO, width:800, height:600, scene:MyScene, physics:{...}}).",
}


def raw_search_game_refs(genre: str) -> List[Dict[str, str]]:
    return _ddg_search(f"best indie {genre} games design inspiration", max_results=5)


def raw_fetch_gamedev_article(url: str) -> str:
    try:
        r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0 QuantumForge/1.0"})
        r.raise_for_status()
        return _clean_html(r.text)
    except Exception as e:
        return f"[fetch failed: {e}]"


def raw_lookup_phaser_docs(topic: str) -> str:
    key = topic.strip().lower()
    for k, v in PHASER_TOPICS.items():
        if k in key or key in k:
            return f"[Phaser::{k}] {v}"
    return "[Phaser] topics: " + ", ".join(PHASER_TOPICS.keys())
