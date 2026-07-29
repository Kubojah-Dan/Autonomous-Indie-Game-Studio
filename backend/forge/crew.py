"""CrewAI pipeline — 10 collaborative agents that forge a full game."""
from __future__ import annotations

import os
import re
import time
from typing import Callable, Dict, Any, Optional

from crewai import Agent, Crew, Process, Task, LLM

from .tools import search_game_refs, fetch_gamedev_article, lookup_phaser_docs

GEMINI_MODEL = "gemini/gemini-2.0-flash"
GROQ_70B = "groq/llama-3.3-70b-versatile"
GROQ_8B = "groq/llama-3.1-8b-instant"


def _mk_llm(model: str, env_key: str, temperature: float = 0.3) -> LLM:
    key = os.getenv(env_key)
    return LLM(model=model, api_key=key if key else None, temperature=temperature)


def build_agents():
    # Use 8b model for light text tasks (30k TPM quota) and 70b model for code & core mechanics
    groq_fast = _mk_llm(GROQ_8B, "GROQ_API_KEY", 0.3)
    groq_heavy = _mk_llm(GROQ_70B, "GROQ_API_KEY", 0.2)
    
    # Try Gemini if key is provided and non-empty
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key and len(gemini_key) > 10 and not gemini_key.startswith("AQ."):
        heavy_llm = _mk_llm(GEMINI_MODEL, "GEMINI_API_KEY", 0.3)
        light_llm = _mk_llm(GEMINI_MODEL, "GEMINI_API_KEY", 0.2)
    else:
        heavy_llm = groq_heavy
        light_llm = groq_fast

    orchestrator = Agent(
        role="OrchestratorAgent",
        goal="Coordinate the ten-stage game forge pipeline and ensure every downstream agent has the context it needs.",
        backstory="A veteran studio producer who has shipped 40+ indie titles.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )
    idea_expander = Agent(
        role="IdeaExpanderAgent",
        goal="Turn a one-line game pitch into a rich, evocative concept document.",
        backstory="A creative director obsessed with elevator pitches and player fantasy.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )
    genre_scout = Agent(
        role="GenreScoutAgent",
        goal="Research 3 indie references from the web that inspire the concept.",
        backstory="A game historian with encyclopedic knowledge of itch.io.",
        llm=light_llm, tools=[search_game_refs, fetch_gamedev_article],
        allow_delegation=False, verbose=False, max_iter=2,
    )
    mechanics = Agent(
        role="MechanicsDesignerAgent",
        goal="Design a tight core loop, controls, win/lose conditions and 3-5 unique mechanics.",
        backstory="A systems designer who worships Sid Meier's 'interesting decisions'.",
        llm=heavy_llm, allow_delegation=False, verbose=False,
    )
    story = Agent(
        role="StoryWriterAgent",
        goal="Write a minimal, evocative narrative and short character bios.",
        backstory="A short-fiction author who writes tight, punchy game lore.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )
    art = Agent(
        role="ArtDirectorAgent",
        goal="Produce 4 short text-to-image prompts for sprites and tilesets.",
        backstory="A pixel-art aficionado who briefs external image AIs.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )
    level = Agent(
        role="LevelDesignerAgent",
        goal="Craft 3 distinct level layouts as ASCII maps.",
        backstory="Grew up making Doom WADs and Zelda dungeons.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )
    coder = Agent(
        role="CodeGeneratorAgent",
        goal="Write a complete, self-contained playable HTML5 Phaser 3 game.",
        backstory="A prolific gamejam coder who ships in hours, not weeks.",
        llm=heavy_llm, tools=[lookup_phaser_docs],
        allow_delegation=False, verbose=False, max_iter=2,
    )
    qa = Agent(
        role="QATesterAgent",
        goal="Read the generated code, catch bugs, and produce a playtest report.",
        backstory="An obsessive QA lead who has broken every game they've touched.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )
    balance = Agent(
        role="BalanceTunerAgent",
        goal="Suggest 5 difficulty tuning parameters with default values.",
        backstory="A live-ops designer who lives inside spreadsheets.",
        llm=light_llm, allow_delegation=False, verbose=False,
    )

    return {
        "orchestrator": orchestrator,
        "idea_expander": idea_expander,
        "genre_scout": genre_scout,
        "mechanics": mechanics,
        "story": story,
        "art": art,
        "level": level,
        "coder": coder,
        "qa": qa,
        "balance": balance,
    }


def build_tasks(idea: str, agents: Dict[str, Agent]):
    return [
        Task(
            description=(
                f"The user pitched a game idea: \"{idea}\".\n"
                "Draft a numbered 5-step production plan for the ten-agent pipeline. "
                "Keep it under 120 words."
            ),
            expected_output="A numbered plan.",
            agent=agents["orchestrator"],
        ),
        Task(
            description=(
                f"Expand the one-liner \"{idea}\" into a full game concept document.\n"
                "Include: Title (invent one), Elevator pitch (1 sentence), Genre, Target audience, "
                "Core fantasy, Unique hook. 180-260 words."
            ),
            expected_output="Concept document.",
            agent=agents["idea_expander"],
        ),
        Task(
            description=(
                f"Given the concept above, use the search_game_refs tool ONCE with the game's genre/keyword. "
                "Then produce a short list of exactly 3 reference games: title, one-line reason it inspires. "
                "Do not perform more than one search."
            ),
            expected_output="3 references.",
            agent=agents["genre_scout"],
        ),
        Task(
            description=(
                "From the concept + references, define:\n"
                "- Core game loop (3-5 bullet steps)\n"
                "- Player controls (keys + effects)\n"
                "- Win condition, Lose condition\n"
                "- 3 to 5 unique mechanics (name + one-line explanation)."
            ),
            expected_output="Mechanics spec.",
            agent=agents["mechanics"],
        ),
        Task(
            description=(
                "Write 2 short narrative paragraphs (opening hook + world setup) "
                "and 2 character bios (name, role, one-line motivation)."
            ),
            expected_output="Narrative + bios.",
            agent=agents["story"],
        ),
        Task(
            description=(
                "Write 4 text-to-image prompts (<= 40 words each) suitable for feeding into any image AI:\n"
                "1) Player sprite  2) Enemy sprite  3) Tileset  4) Cover art.\n"
                "Format:\n"
                "PROMPT_PLAYER: ...\n"
                "PROMPT_ENEMY: ...\n"
                "PROMPT_TILESET: ...\n"
                "PROMPT_COVER: ..."
            ),
            expected_output="4 prompts.",
            agent=agents["art"],
        ),
        Task(
            description=(
                "Design 3 level layouts as ASCII grids exactly 20 columns wide by 8 rows tall. "
                "Use symbols: # wall, . floor, P player start, E enemy, X goal. "
                "Prefix each map with a title line like 'LEVEL 1 :: <name>'. "
                "Separate maps with a blank line."
            ),
            expected_output="3 ASCII maps.",
            agent=agents["level"],
        ),
        Task(
            description=(
                "Write a COMPLETE, SELF-CONTAINED, PLAYABLE HTML5 game using Phaser 3 from CDN.\n"
                "STRICT RULES — read carefully:\n"
                " * Output MUST be a single HTML document starting with '<!DOCTYPE html>' and ending with '</html>'.\n"
                " * NO markdown fences, NO commentary. Just the raw HTML.\n"
                " * Include the Phaser CDN: https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js\n"
                " * All JS inline in a <script> tag.\n"
                " * Canvas size 800x600, background #0A0A0F.\n"
                " * DO NOT load any external images or audio (no this.load.image calls). "
                "Draw all sprites with Phaser Graphics (rectangles, circles).\n"
                " * Implement: player with keyboard controls, at least one enemy/obstacle, "
                "score UI, game-over state with restart on SPACE.\n"
                " * Style all in-game text as neon green (#00FF41) monospace.\n"
                " * Reflect the mechanics designed above."
            ),
            expected_output="Full HTML document.",
            agent=agents["coder"],
        ),
        Task(
            description=(
                "You just received the generated game HTML above. Review it and produce a compact playtest report:\n"
                "- FUN_SCORE: 1-10\n"
                "- BUGS: bullet list (or 'none')\n"
                "- PATCHES: brief suggestions\n"
                "- VERDICT: PASS or NEEDS_WORK\n"
                "Keep under 150 words."
            ),
            expected_output="Playtest report.",
            agent=agents["qa"],
        ),
        Task(
            description=(
                "Propose exactly 5 balance-tuning parameters for this game as a table:\n"
                "PARAM | DEFAULT | EFFECT\n"
                "-----+---------+-------\n"
                "(five rows, one per parameter, concise)."
            ),
            expected_output="5-row balance table.",
            agent=agents["balance"],
        ),
    ]

def _run_with_retry(task, log, agent_name, retries: int = 3):
    """Run a CrewAI task with backoff on rate-limit errors."""
    for attempt in range(retries + 1):
        try:
            return task.execute_sync()
        except Exception as e:
            msg = str(e)
            if ("RateLimit" in msg or "429" in msg or "rate limit" in msg.lower()) and attempt < retries:
                wait_s = 8 + attempt * 6
                log(agent_name, f"[warn] rate limited — retrying in {wait_s}s", level="warn")
                time.sleep(wait_s)
                continue
            raise


def extract_html(text: str) -> str:
    """Pull out the HTML document from a possibly-messy LLM output."""
    if not text:
        return ""
    m = re.search(r"<!DOCTYPE html>.*?</html>", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(0)
    m = re.search(r"```(?:html)?\s*(<!DOCTYPE html>.*?</html>)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1)
    return ""


class ForgePipeline:
    """Manual sequential runner around CrewAI Agents so we can broadcast
    per-agent progress events over WebSocket without waiting for the whole
    Crew.kickoff() to finish."""

    STAGE_NAMES = [
        ("OrchestratorAgent",     "Planning production pipeline"),
        ("IdeaExpanderAgent",     "Expanding one-liner into concept"),
        ("GenreScoutAgent",       "Scouting the web for references"),
        ("MechanicsDesignerAgent","Designing core loop + controls"),
        ("StoryWriterAgent",      "Writing narrative + characters"),
        ("ArtDirectorAgent",      "Drafting sprite prompts"),
        ("LevelDesignerAgent",    "Laying out ASCII level maps"),
        ("CodeGeneratorAgent",    "Generating Phaser.js game code"),
        ("QATesterAgent",         "Play-testing the build"),
        ("BalanceTunerAgent",     "Tuning difficulty parameters"),
    ]

    ARTIFACT_KEYS = [
        "plan", "concept", "references", "mechanics", "story",
        "sprite_prompts", "levels", "code", "qa_report", "balance",
    ]

    def __init__(self, idea: str, emit: Callable[[Dict[str, Any]], None]):
        self.idea = idea
        self.emit = emit
        self.agents = build_agents()
        self.tasks = build_tasks(idea, self.agents)
        self.artifacts: Dict[str, str] = {}

    def _log(self, stream: str, text: str, level: str = "info"):
        self.emit({"type": "log", "stream": stream, "text": text, "level": level})

    def _stage(self, index: int, status: str, extra: Optional[dict] = None):
        payload = {
            "type": "stage",
            "index": index,
            "agent": self.STAGE_NAMES[index][0],
            "title": self.STAGE_NAMES[index][1],
            "status": status,
        }
        if extra:
            payload.update(extra)
        self.emit(payload)

    def _artifact(self, key: str, content: str):
        self.artifacts[key] = content
        self.emit({"type": "artifact", "key": key, "content": content})

    def run(self) -> Dict[str, str]:
        self._log("system", f"[FORGE] booting pipeline for idea: {self.idea!r}")

        for i, task in enumerate(self.tasks):
            if i > 0:
                time.sleep(2.5)  # Pace agent calls to prevent TPM spikes on Groq free tier

            key = self.ARTIFACT_KEYS[i]
            agent_name, title = self.STAGE_NAMES[i]
            self._stage(i, "running")
            self._log(agent_name, f"> {title}...")

            try:
                # Feed prior context by concatenating previous outputs for the LLM
                context = self._build_context(i)
                task.description = context + "\n\n" + task.description
                output = _run_with_retry(task, self._log, agent_name)
                result_text = str(output.raw if hasattr(output, "raw") else output)
            except Exception as e:
                self._log(agent_name, f"[warn] {e}", level="warn")
                result_text = f"[{agent_name} failed: {e}]"

            if key == "code":
                html = extract_html(result_text)
                if not html:
                    self._log(agent_name, "[warn] no <!DOCTYPE html> found — using fallback template", level="warn")
                    html = _fallback_game_html(self.idea)
                result_text = html

            self._artifact(key, result_text)
            preview = (result_text[:220] + "…") if len(result_text) > 220 else result_text
            self._log(agent_name, preview.replace("\n", " ⏎ "))
            self._stage(i, "done")

        return self.artifacts

    def _build_context(self, i: int) -> str:
        if i == 0:
            return ""
        # Keep context lean to stay under Groq TPM. Include a short summary of
        # each prior artifact, capped tight. QA needs full code; everyone else
        # gets a stub.
        parts = ["--- PRIOR PIPELINE CONTEXT ---"]
        include_code = (i == 8)  # QATesterAgent needs the full HTML
        for j in range(i):
            k = self.ARTIFACT_KEYS[j]
            if k not in self.artifacts:
                continue
            snippet = self.artifacts[k]
            if k == "code":
                snippet = snippet if include_code else "<HTML omitted>"
            cap = 2500 if (include_code and k == "code") else 350
            parts.append(f"[{self.STAGE_NAMES[j][0]}]\n{snippet[:cap]}")
        parts.append("--- END CONTEXT ---")
        return "\n".join(parts)


def _fallback_game_html(idea: str) -> str:
    """Guarantees a playable prototype even if the LLM code stage fails."""
    safe_idea = idea.replace('"', "'")[:80]
    return (
        "<!DOCTYPE html>\n<html><head><meta charset='utf-8'/>"
        "<title>QuantumForge Prototype</title>"
        "<script src='https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js'></script>"
        "<style>body{margin:0;background:#0A0A0F;color:#00FF41;font-family:monospace}</style>"
        "</head><body>"
        "<script>"
        "class Main extends Phaser.Scene{"
        "constructor(){super('m')}"
        "create(){"
        f"this.add.text(20,20,'PROTOTYPE :: {safe_idea}',{{color:'#00FF41',fontFamily:'monospace',fontSize:'18px'}});"
        "this.p=this.add.rectangle(400,500,32,32,0x00ff41);"
        "this.physics.add.existing(this.p);this.p.body.setCollideWorldBounds(true);"
        "this.cursors=this.input.keyboard.createCursorKeys();"
        "this.enemies=this.physics.add.group();"
        "for(let i=0;i<5;i++){let e=this.add.rectangle(Phaser.Math.Between(50,750),Phaser.Math.Between(50,300),24,24,0xff00e5);"
        "this.physics.add.existing(e);e.body.setVelocity(Phaser.Math.Between(-100,100),Phaser.Math.Between(-100,100));"
        "e.body.setBounce(1,1);e.body.setCollideWorldBounds(true);this.enemies.add(e);}"
        "this.score=0;this.scoreText=this.add.text(20,50,'SCORE: 0',{color:'#00F0FF',fontFamily:'monospace',fontSize:'18px'});"
        "this.physics.add.overlap(this.p,this.enemies,()=>{this.scene.restart();});"
        "}"
        "update(){"
        "if(this.cursors.left.isDown)this.p.body.setVelocityX(-200);"
        "else if(this.cursors.right.isDown)this.p.body.setVelocityX(200);"
        "else this.p.body.setVelocityX(0);"
        "if(this.cursors.up.isDown)this.p.body.setVelocityY(-200);"
        "else if(this.cursors.down.isDown)this.p.body.setVelocityY(200);"
        "else this.p.body.setVelocityY(0);"
        "this.score+=1;this.scoreText.setText('SCORE: '+this.score);"
        "}"
        "}"
        "new Phaser.Game({type:Phaser.AUTO,width:800,height:600,backgroundColor:'#0A0A0F',"
        "physics:{default:'arcade',arcade:{gravity:{y:0}}},scene:Main});"
        "</script></body></html>"
    )
