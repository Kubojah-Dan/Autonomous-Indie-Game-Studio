import React, { useEffect } from "react";

const LINES = [
  "[BOOT] BIOS v1.0.0 :: QUANTUMFORGE VM",
  "[BOOT] Checking neon subsystems ................ OK",
  "[BOOT] Priming CrewAI 10-agent pipeline ......... OK",
  "[BOOT] Mounting /generated-games ................ OK",
  "[BOOT] Handshaking Gemini (flash-2.0) ........... OK",
  "[BOOT] Handshaking Groq (llama-3.3-70b) ......... OK",
  "[BOOT] Chrome-MCP tool bus online ............... OK",
  "[BOOT] Loading pre-forged demo :: NEON RUNNER ... OK",
  "\u00a0",
  "ACCESSING QUANTUMFORGE...",
];

const STEP_MS = 140;
const FINISH_MS = LINES.length * STEP_MS + 500;

export default function BootSequence({ onDone }) {
  useEffect(() => {
    const id = window.setTimeout(() => {
      if (onDone) onDone();
    }, FINISH_MS);
    return () => window.clearTimeout(id);
  }, [onDone]);

  return (
    <div className="qf-boot-screen font-mono2" data-testid="boot-sequence">
      <div className="crt-scanlines" />
      <div className="font-display text-3xl glow-green">[QUANTUMFORGE::v1.0]</div>
      <div className="text-xs text-[color:var(--qf-cyan)] uppercase tracking-widest">
        Autonomous Indie Game Dev Studio :: booting
      </div>
      <div className="qf-hr" />
      {LINES.map((l, idx) => (
        <div
          key={idx}
          className={`qf-boot-reveal text-sm ${l.startsWith("ACCESSING") ? "font-display text-2xl glow-magenta mt-4" : "text-[color:var(--qf-green)]"}`}
          style={{ animationDelay: `${idx * STEP_MS}ms` }}
        >
          {l}
          {idx === LINES.length - 1 && <span className="qf-cursor" />}
        </div>
      ))}
    </div>
  );
}
