import React, { useMemo, useState } from "react";
import TerminalWindow from "@/components/TerminalWindow";

const LABELS = {
  plan: "PIPELINE PLAN",
  concept: "GAME CONCEPT",
  references: "GENRE SCOUT :: REFERENCES",
  mechanics: "MECHANICS SPEC",
  story: "NARRATIVE + CHARACTERS",
  sprite_prompts: "SPRITE PROMPTS",
  levels: "LEVEL LAYOUTS",
  code: "PHASER CODE",
  qa_report: "QA PLAYTEST REPORT",
  balance: "BALANCE TUNING",
};

const ORDER = ["plan", "concept", "references", "mechanics", "story", "sprite_prompts", "levels", "qa_report", "balance", "code"];

export default function ArtifactViewer({ artifacts }) {
  const keys = useMemo(() => ORDER.filter((k) => artifacts[k]), [artifacts]);
  const [active, setActive] = useState(keys[0] || "");

  React.useEffect(() => {
    if (!active && keys.length) setActive(keys[0]);
  }, [keys, active]);

  if (!keys.length) {
    return (
      <TerminalWindow title="[ARTIFACTS]" tone="cyan" testId="artifacts-empty">
        <div className="text-sm text-[color:var(--qf-green)]/70">
          <span className="glow-cyan">// awaiting forge output</span>
          <div className="qf-hr" />
          <pre className="text-xs opacity-80">{`  when the pipeline runs, this pane fills with:
    - concept doc
    - reference scouting
    - mechanics + level maps
    - sprite prompts
    - phaser code
    - QA playtest report`}</pre>
        </div>
      </TerminalWindow>
    );
  }

  return (
    <TerminalWindow
      title="[ARTIFACTS]"
      tone="cyan"
      right={`${keys.length}/10 delivered`}
      testId="artifacts-panel"
    >
      <div className="flex flex-wrap gap-1 mb-3">
        {keys.map((k) => (
          <button
            key={k}
            onClick={() => setActive(k)}
            data-testid={`artifact-tab-${k}`}
            className={`text-[11px] font-mono2 px-2 py-1 border ${active === k ? "bg-[color:var(--qf-cyan)] text-[color:var(--qf-bg)] border-[color:var(--qf-cyan)]" : "border-[color:var(--qf-cyan)]/50 text-[color:var(--qf-cyan)]/90 hover:border-[color:var(--qf-cyan)]"}`}
          >
            {LABELS[k] || k.toUpperCase()}
          </button>
        ))}
      </div>
      <pre
        className="text-[13px] whitespace-pre-wrap break-words font-mono2 text-[color:var(--qf-green)]"
        data-testid={`artifact-content-${active}`}
      >
        {artifacts[active]}
      </pre>
    </TerminalWindow>
  );
}
