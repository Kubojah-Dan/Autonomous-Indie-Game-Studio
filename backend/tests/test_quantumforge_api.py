"""QuantumForge AI — backend API tests.

Covers:
  - /api/health
  - /api/vault (seeded neon-runner)
  - /api/game/{id} (metadata + artifacts)
  - /api/game/{id}/play (HTML with Phaser CDN)
  - /api/game/{id}/download (ZIP)
  - /api/mcp/search, /api/mcp/phaser, /api/mcp/fetch
  - /api/forge/new + poll + WebSocket stream
"""
from __future__ import annotations

import io
import json
import os
import time
import zipfile

import pytest
import requests
import websocket  # websocket-client

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/") if os.environ.get(
    "REACT_APP_BACKEND_URL"
) else None
if not BASE_URL:
    # tests run inside the same repo; fall back to env from frontend/.env
    with open("/app/frontend/.env") as fh:
        for ln in fh:
            if ln.startswith("REACT_APP_BACKEND_URL"):
                BASE_URL = ln.split("=", 1)[1].strip().rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

WS_URL = BASE_URL.replace("https://", "wss://").replace("http://", "ws://")

REQUIRED_ARTIFACT_KEYS = [
    "plan", "concept", "references", "mechanics", "story",
    "sprite_prompts", "levels", "code", "qa_report", "balance",
]

DEMO_ID = "neon-runner"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


# ---------- health ----------
def test_health(s):
    r = s.get(f"{BASE_URL}/api/health", timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert j.get("ok") is True
    assert j.get("service") == "quantumforge"


# ---------- vault ----------
def test_vault_lists_demo(s):
    r = s.get(f"{BASE_URL}/api/vault", timeout=15)
    assert r.status_code == 200
    games = r.json()["games"]
    ids = [g["id"] for g in games]
    assert DEMO_ID in ids
    demo = next(g for g in games if g["id"] == DEMO_ID)
    assert demo["status"] == "done"
    assert demo["demo"] is True


# ---------- demo meta / play / download ----------
def test_demo_meta(s):
    r = s.get(f"{BASE_URL}/api/game/{DEMO_ID}", timeout=15)
    assert r.status_code == 200
    doc = r.json()
    assert doc["id"] == DEMO_ID
    assert doc["idea"]
    arts = doc.get("artifacts", {})
    for k in REQUIRED_ARTIFACT_KEYS:
        assert k in arts and arts[k], f"missing artifact {k}"


def test_demo_play_html(s):
    r = s.get(f"{BASE_URL}/api/game/{DEMO_ID}/play", timeout=15)
    assert r.status_code == 200
    html = r.text
    assert html.lstrip().lower().startswith("<!doctype html>")
    assert "phaser" in html.lower()
    assert "cdn.jsdelivr.net/npm/phaser" in html or "phaser.min.js" in html


def test_demo_download_zip(s):
    r = s.get(f"{BASE_URL}/api/game/{DEMO_ID}/download", timeout=30)
    assert r.status_code == 200
    assert "application/zip" in r.headers.get("content-type", "").lower()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    names = z.namelist()
    assert any(n.endswith("index.html") for n in names)


# ---------- mcp endpoints ----------
def test_mcp_search(s):
    r = s.get(f"{BASE_URL}/api/mcp/search", params={"genre": "platformer"}, timeout=30)
    assert r.status_code == 200
    j = r.json()
    assert "results" in j
    assert isinstance(j["results"], list)


def test_mcp_phaser(s):
    r = s.get(f"{BASE_URL}/api/mcp/phaser", params={"topic": "physics"}, timeout=15)
    assert r.status_code == 200
    j = r.json()
    assert "doc" in j
    assert "phaser" in j["doc"].lower()


def test_mcp_fetch(s):
    r = s.post(
        f"{BASE_URL}/api/mcp/fetch",
        json={"url": "https://example.com"},
        timeout=30,
    )
    assert r.status_code == 200
    j = r.json()
    assert "text" in j
    assert isinstance(j["text"], str)


def test_mcp_fetch_missing_url(s):
    r = s.post(f"{BASE_URL}/api/mcp/fetch", json={}, timeout=15)
    assert r.status_code == 400


# ---------- forge (WS + pipeline) ----------
@pytest.fixture(scope="module")
def forged_game(s):
    """Forge a new game and poll to completion (up to 3 min)."""
    r = s.post(
        f"{BASE_URL}/api/forge/new",
        json={"idea": "a simple 2D dodge game"},
        timeout=30,
    )
    assert r.status_code == 200, r.text
    j = r.json()
    assert "game_id" in j and "stream_url" in j
    game_id = j["game_id"]

    # Connect WebSocket in a background thread to collect events
    ws_events = []
    ws_url = f"{WS_URL}/api/agents/stream/{game_id}"
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
    except Exception as e:
        ws = None
        print(f"WS connect failed: {e}")

    import threading

    def _reader():
        try:
            while ws:
                msg = ws.recv()
                if not msg:
                    break
                try:
                    ev = json.loads(msg)
                except Exception:
                    continue
                ws_events.append(ev)
                if ev.get("type") in {"done", "error"}:
                    break
        except Exception as e:
            print(f"WS reader stopped: {e}")

    t = None
    if ws:
        t = threading.Thread(target=_reader, daemon=True)
        t.start()

    # Poll REST until done
    deadline = time.time() + 210  # 3.5 min
    status = "running"
    doc = None
    while time.time() < deadline:
        rr = s.get(f"{BASE_URL}/api/game/{game_id}", timeout=15)
        if rr.status_code == 200:
            doc = rr.json()
            status = doc.get("status")
            if status in {"done", "error"}:
                break
        time.sleep(4)

    if t:
        t.join(timeout=5)
        try:
            ws.close()
        except Exception:
            pass

    return {"game_id": game_id, "status": status, "doc": doc, "events": ws_events}


def test_forge_completes(forged_game):
    assert forged_game["status"] == "done", f"status={forged_game['status']}"
    arts = forged_game["doc"].get("artifacts", {})
    missing = [k for k in REQUIRED_ARTIFACT_KEYS if not arts.get(k)]
    assert not missing, f"missing/empty artifacts: {missing}"


def test_forged_play_html(s, forged_game):
    if forged_game["status"] != "done":
        pytest.skip("forge did not complete")
    gid = forged_game["game_id"]
    r = s.get(f"{BASE_URL}/api/game/{gid}/play", timeout=15)
    assert r.status_code == 200
    html = r.text.lower()
    assert "<!doctype html>" in html
    assert "phaser" in html


def test_ws_events(forged_game):
    events = forged_game["events"]
    if not events:
        pytest.skip("no WS events captured (connection may have failed)")
    types = [e.get("type") for e in events]
    print(f"WS event types collected: {types[:40]}")
    assert any(t == "stage" for t in types), f"no stage events: {types}"
    assert any(t == "artifact" for t in types), f"no artifact events: {types}"
    assert any(t == "done" for t in types), f"no done event: {types}"
