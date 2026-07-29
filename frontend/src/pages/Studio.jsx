import React, { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import { toast } from "sonner";
import TerminalWindow from "@/components/TerminalWindow";
import AgentTerminal from "@/components/AgentTerminal";
import ArtifactViewer from "@/components/ArtifactViewer";
import GamePreview from "@/components/GamePreview";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND}/api`;

const STAGE_TEMPLATE = [
  ["OrchestratorAgent",     "Planning production pipeline"],
  ["IdeaExpanderAgent",     "Expanding one-liner into concept"],
  ["GenreScoutAgent",       "Scouting the web for references"],
  ["MechanicsDesignerAgent","Designing core loop + controls"],
  ["StoryWriterAgent",      "Writing narrative + characters"],
  ["ArtDirectorAgent",      "Drafting sprite prompts"],
  ["LevelDesignerAgent",    "Laying out ASCII level maps"],
  ["CodeGeneratorAgent",    "Generating Phaser.js game code"],
  ["QATesterAgent",         "Play-testing the build"],
  ["BalanceTunerAgent",     "Tuning difficulty parameters"],
];

const ACHIEVEMENT_MAP = {
  0: "PLAN LOCKED",
  1: "CONCEPT UNLOCKED",
  2: "SCOUT COMPLETE",
  3: "MECHANICS FORGED",
  4: "STORY BURNED-IN",
  5: "SPRITES BRIEFED",
  6: "LEVELS COMPILED",
  7: "CODE SHIPPED",
  8: "QA CLEARED",
  9: "BALANCE TUNED",
};

export default function Studio() {
  const [idea, setIdea] = useState("");
  const [gameId, setGameId] = useState(null);
  const [lines, setLines] = useState([]);
  const [stages, setStages] = useState(STAGE_TEMPLATE.map(([a, t]) => ({ agent: a, title: t, status: "pending" })));
  const [artifacts, setArtifacts] = useState({});
  const [phase, setPhase] = useState("idle"); // idle | running | done | error
  const wsRef = useRef(null);

  // Load pre-forged demo on mount so the UI is populated on first visit
  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/game/neon-runner`);
        if (r.data) {
          setGameId("neon-runner");
          setArtifacts(r.data.artifacts || {});
          setStages(STAGE_TEMPLATE.map(([a, t]) => ({ agent: a, title: t, status: "done" })));
          setPhase("done");
        }
      } catch (e) { /* ignore */ }
    })();
  }, []);

  const wsUrl = useMemo(() => {
    if (!BACKEND) return null;
    return BACKEND.replace(/^http/, "ws");
  }, []);

  const handleEvent = (evt) => {
    setLines((prev) => [...prev, evt]);
    if (evt.type === "stage") {
      setStages((prev) => prev.map((s, i) => (i === evt.index ? { ...s, status: evt.status } : s)));
      if (evt.status === "done" && ACHIEVEMENT_MAP[evt.index]) {
        toast(`>> ACHIEVEMENT :: ${ACHIEVEMENT_MAP[evt.index]}`, { duration: 3200 });
      }
    } else if (evt.type === "artifact") {
      setArtifacts((prev) => ({ ...prev, [evt.key]: evt.content }));
    } else if (evt.type === "done") {
      setPhase("done");
      toast(">> BUILD SUCCESSFUL :: PROTOTYPE READY", { duration: 4000 });
    } else if (evt.type === "error") {
      setPhase("error");
      toast(`>> BUILD FAILED :: ${evt.error}`, { duration: 5000 });
    }
  };

  const forge = async () => {
    if (!idea.trim() || phase === "running") return;
    // reset
    setLines([{ type: "user", text: `forge new game: ${idea.trim()}` }]);
    setStages(STAGE_TEMPLATE.map(([a, t]) => ({ agent: a, title: t, status: "pending" })));
    setArtifacts({});
    setPhase("running");
    try {
      const r = await axios.post(`${API}/forge/new`, { idea: idea.trim() });
      const id = r.data.game_id;
      setGameId(id);
      const ws = new WebSocket(`${wsUrl}/api/agents/stream/${id}`);
      wsRef.current = ws;
      ws.onmessage = (m) => {
        try { handleEvent(JSON.parse(m.data)); } catch (e) { console.error(e); }
      };
      ws.onerror = () => toast(">> WS ERROR :: connection failed");
      ws.onclose = () => { /* end */ };
    } catch (e) {
      setPhase("error");
      toast(`>> FORGE ERROR :: ${e?.response?.data?.detail || e.message}`);
    }
  };

  const onKey = (e) => {
    if (e.key === "Enter") forge();
  };

  const doneCount = stages.filter((s) => s.status === "done").length;

  return (
    <div className="p-3 md:p-4 space-y-3">
      <TerminalWindow
        title="[PROMPT :: FORGE COMMAND]"
        right={phase === "running" ? "FORGING..." : phase === "done" ? "READY" : phase === "error" ? "ERROR" : "IDLE"}
        testId="prompt-window"
      >
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-mono2 text-[color:var(--qf-cyan)] text-lg">&gt;</span>
          <span className="font-mono2 text-[color:var(--qf-cyan)] text-lg">forge new game:</span>
          <input
            className="qf-input min-w-[280px]"
            data-testid="idea-input"
            value={idea}
            placeholder="a cyberpunk parkour deliverer chased by drones"
            onChange={(e) => setIdea(e.target.value)}
            onKeyDown={onKey}
            disabled={phase === "running"}
          />
          <span className="qf-cursor" />
          <button
            className="qf-btn"
            data-testid="forge-button"
            onClick={forge}
            disabled={phase === "running" || !idea.trim()}
          >
            {phase === "running" ? "Forging..." : "Forge"}
          </button>
        </div>
        <div className="qf-hr" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1">
          {stages.map((s, i) => (
            <div key={i} className="qf-stage-row" data-testid={`stage-${i}`}>
              <span className={`dot ${s.status}`} />
              <span className="text-[color:var(--qf-cyan)] w-6">[{String(i).padStart(2, "0")}]</span>
              <span className="text-[color:var(--qf-green)]">{s.agent}</span>
              <span className="text-[color:var(--qf-green)]/60 truncate">:: {s.title}</span>
            </div>
          ))}
        </div>
        <div className="text-xs mt-2 text-[color:var(--qf-cyan)]/80" data-testid="stage-progress">
          progress :: {doneCount} / 10 agents complete
        </div>
      </TerminalWindow>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3 h-[calc(100vh-360px)] min-h-[520px]">
        <TerminalWindow
          title="[AGENT STREAM :: LIVE]"
          right={phase.toUpperCase()}
          className="h-full"
          testId="stream-window"
        >
          <div className="h-full min-h-[420px]">
            <AgentTerminal lines={lines} />
          </div>
        </TerminalWindow>

        <div className="flex flex-col gap-3 h-full min-h-0">
          <div className="flex-1 min-h-0">
            <ArtifactViewer artifacts={artifacts} />
          </div>
          <div className="flex-1 min-h-0">
            <GamePreview gameId={phase === "done" ? gameId : null} backendUrl={BACKEND} />
          </div>
        </div>
      </div>
    </div>
  );
}
