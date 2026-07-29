# QuantumForge AI

**An Autonomous Indie Game Dev Studio** that turns a one-line game idea into a
playable HTML5 prototype using **10 collaborative AI agents** orchestrated by
CrewAI. Ships a cyberpunk retro-terminal UI, a live agent log stream over
WebSocket, and a downloadable ZIP of every artifact (concept, mechanics,
sprite prompts, level maps, Phaser 3 code, QA report, balance table).

```
[QUANTUMFORGE::v1.0]   Autonomous Indie Game Dev Studio
```

---

## 1. The 10 Agents

| # | Agent | LLM | Deliverable |
|---|---|---|---|
| 00 | `OrchestratorAgent`      | Groq  | Pipeline production plan |
| 01 | `IdeaExpanderAgent`      | Groq  | Full concept doc from one-liner |
| 02 | `GenreScoutAgent`        | Groq  | Web-scraped inspiration references (via Chrome MCP) |
| 03 | `MechanicsDesignerAgent` | Groq  | Core loop, controls, win/lose |
| 04 | `StoryWriterAgent`       | Groq  | Narrative + character bios |
| 05 | `ArtDirectorAgent`       | Groq  | 4 sprite/tileset text-to-image prompts |
| 06 | `LevelDesignerAgent`     | Groq  | 3 ASCII level layouts |
| 07 | `CodeGeneratorAgent`     | Groq  | Complete self-contained Phaser 3 HTML |
| 08 | `QATesterAgent`          | Groq  | Playtest report + verdict |
| 09 | `BalanceTunerAgent`      | Groq  | 5 difficulty-tuning parameters |

Both **Gemini** (`gemini/gemini-2.0-flash`) and **Groq** (`groq/llama-3.3-70b-versatile`)
are wired via CrewAI + LiteLLM. If your Gemini key is quota-exhausted, the
pipeline transparently uses Groq for every stage (fast + generous free tier).
Swap in your own Gemini key in `.env` to route the creative stages back through
Gemini (see `backend/forge/crew.py :: build_agents`).

## 2. Chrome MCP tools

The `mcp-chrome` micro-service exposes three tools that the `GenreScoutAgent`
uses to research the web:

| Tool | HTTP endpoint | Purpose |
|---|---|---|
| `search_game_refs(genre)`     | `GET  /tools/search_game_refs?genre=...` | DuckDuckGo web search |
| `fetch_gamedev_article(url)`  | `POST /tools/fetch_gamedev_article`      | Fetch + clean article text |
| `lookup_phaser_docs(topic)`   | `GET  /tools/lookup_phaser_docs?topic=...` | Phaser 3 doc snippets |

## 3. Run it (docker-compose)

```bash
cp .env.example .env
# edit GEMINI_API_KEY / GROQ_API_KEY if you want to swap in your own
docker-compose up --build
```

- Frontend :: <http://localhost:3000>
- Backend  :: <http://localhost:8001>  (API + WebSocket)
- MCP      :: <http://localhost:8811>
- Mongo    :: `mongodb://localhost:27017/quantumforge`
- Generated games :: mounted volume `./generated-games/{game_id}/`

## 4. HTTP API

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/forge/new`                       | `{idea}` → `{game_id, stream_url}` |
| WS   | `/api/agents/stream/{game_id}`         | Live agent events |
| GET  | `/api/vault`                            | List all forged games |
| GET  | `/api/game/{id}`                        | Game metadata + artifacts |
| GET  | `/api/game/{id}/play`                   | Serve playable HTML |
| GET  | `/api/game/{id}/download`               | Download `.zip` |
| GET  | `/api/mcp/search?genre=...`             | MCP :: search_game_refs |
| GET  | `/api/mcp/phaser?topic=...`             | MCP :: lookup_phaser_docs |
| POST | `/api/mcp/fetch`                        | MCP :: fetch_gamedev_article |
| GET  | `/api/health`                           | Liveness |

WebSocket event schema (JSON per line):

```json
{ "type": "stage",   "index": 0, "agent": "OrchestratorAgent", "title": "...", "status": "running|done" }
{ "type": "log",     "stream": "IdeaExpanderAgent", "text": "...", "level": "info|warn|error" }
{ "type": "artifact","key": "concept", "content": "..." }
{ "type": "done",    "game_id": "abc123" }
```

## 5. Pre-forged demo

A pre-forged demo game **`Neon Runner`** is seeded on first boot — visible in
the Vault and playable at
<http://localhost:8001/api/game/neon-runner/play>. It's a one-button Phaser
endless runner where you dodge magenta debt-collector drones.

## 6. Project structure

```
quantumforge-ai/
├── backend/               FastAPI + CrewAI (10 agents)
│   ├── server.py
│   ├── forge/
│   │   ├── crew.py        the 10-agent sequential pipeline
│   │   ├── tools.py       CrewAI @tool wrappers for MCP tools
│   │   ├── game_writer.py file/zip output
│   │   └── demo.py        seeded Neon Runner
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/              React + xterm.js + Tailwind
│   ├── src/
│   │   ├── App.js
│   │   ├── pages/
│   │   │   ├── Studio.jsx  main split-pane view
│   │   │   ├── Vault.jsx   grid of forged games
│   │   │   └── Play.jsx    single-game player
│   │   └── components/
│   │       ├── BootSequence.jsx
│   │       ├── TerminalWindow.jsx
│   │       ├── AgentTerminal.jsx  (xterm)
│   │       ├── ArtifactViewer.jsx
│   │       ├── GamePreview.jsx
│   │       └── GameCard.jsx
│   └── Dockerfile
├── mcp-chrome/            Chrome-MCP-style micro-service
│   ├── app.py
│   ├── tools.py
│   ├── requirements.txt
│   └── Dockerfile
├── generated-games/       output volume — one folder per forged game_id
├── docker-compose.yml
├── .env.example
├── VSCODE_SETUP.md
└── README.md
```

## 7. Design language

Pure retro-cyberpunk terminal — pitch-black `#0A0A0F` background, phosphor
green `#00FF41`, hot cyan `#00F0FF`, magenta `#FF00E5`, `VT323` + `IBM Plex
Mono` fonts, CRT scanline overlay, glitch-on-hover, ASCII banner, boot-up
sequence, blinking cursor, and 8-bit style achievement toasts.

