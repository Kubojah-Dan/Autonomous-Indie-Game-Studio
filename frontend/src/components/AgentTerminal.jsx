import React, { useEffect, useRef } from "react";
import { Terminal } from "xterm";
import { FitAddon } from "xterm-addon-fit";
import "xterm/css/xterm.css";

const COLOR = {
  system: "\x1b[38;5;51m",   // cyan
  info: "\x1b[38;5;46m",     // green
  warn: "\x1b[38;5;201m",    // magenta
  error: "\x1b[38;5;196m",   // red
  reset: "\x1b[0m",
  dim: "\x1b[2m",
  bold: "\x1b[1m",
};

const AGENT_COLORS = [
  "\x1b[38;5;51m",  // cyan
  "\x1b[38;5;46m",  // green
  "\x1b[38;5;201m", // magenta
  "\x1b[38;5;227m", // yellow
  "\x1b[38;5;213m", // pink
  "\x1b[38;5;123m", // pale cyan
  "\x1b[38;5;154m", // pale green
  "\x1b[38;5;208m", // orange
  "\x1b[38;5;99m",  // violet
  "\x1b[38;5;231m", // white
];

function colorForAgent(agent) {
  if (!agent) return COLOR.info;
  let s = 0; for (const c of agent) s = (s + c.charCodeAt(0)) % 997;
  return AGENT_COLORS[s % AGENT_COLORS.length];
}

const AgentTerminal = React.forwardRef(function AgentTerminal({ lines }, ref) {
  const containerRef = useRef(null);
  const termRef = useRef(null);
  const fitRef = useRef(null);
  const writtenRef = useRef(0);

  useEffect(() => {
    const term = new Terminal({
      convertEol: true,
      cursorBlink: true,
      fontFamily: "'IBM Plex Mono', ui-monospace, monospace",
      fontSize: 13,
      theme: {
        background: "#0A0A0F",
        foreground: "#00FF41",
        cursor: "#00FF41",
        selectionBackground: "#00FF4140",
      },
      allowTransparency: true,
      scrollback: 4000,
    });
    const fit = new FitAddon();
    term.loadAddon(fit);
    term.open(containerRef.current);
    // xterm's fit() reads container dimensions which may be 0 pre-layout —
    // defer to next frame to avoid "reading dimensions of undefined".
    const safeFit = () => {
      try {
        const el = containerRef.current;
        if (el && el.clientWidth > 0 && el.clientHeight > 0) fit.fit();
      } catch (e) { /* ignore */ }
    };
    requestAnimationFrame(safeFit);
    termRef.current = term;
    fitRef.current = fit;

    term.writeln(`${COLOR.system}[QUANTUMFORGE] terminal ready. awaiting forge command...${COLOR.reset}`);
    term.writeln(`${COLOR.dim}    type your idea in the prompt below and hit ENTER${COLOR.reset}`);

    const ro = new ResizeObserver(() => { safeFit(); });
    ro.observe(containerRef.current);

    if (ref) {
      if (typeof ref === "function") ref(term); else ref.current = term;
    }
    return () => { ro.disconnect(); term.dispose(); };
  }, []); // eslint-disable-line

  useEffect(() => {
    const term = termRef.current;
    if (!term) return;
    for (let i = writtenRef.current; i < lines.length; i++) {
      const ln = lines[i];
      const agentColor = colorForAgent(ln.agent);
      if (ln.type === "stage") {
        const status = ln.status?.toUpperCase() || "";
        const dot = ln.status === "done" ? "✓" : ln.status === "running" ? "▶" : "·";
        term.writeln(`${COLOR.bold}${agentColor}[${String(ln.index).padStart(2, "0")}]${COLOR.reset} ${agentColor}${ln.agent}${COLOR.reset} ${COLOR.dim}::${COLOR.reset} ${ln.title} ${COLOR.dim}${dot} ${status}${COLOR.reset}`);
      } else if (ln.type === "log") {
        const bucket = ln.level === "warn" ? COLOR.warn : ln.level === "error" ? COLOR.error : agentColor;
        term.writeln(`  ${bucket}${(ln.stream || "").padEnd(24, " ")}${COLOR.reset} ${ln.text}`);
      } else if (ln.type === "done") {
        term.writeln(`${COLOR.bold}${COLOR.info}[DONE] pipeline complete — game_id=${ln.game_id}${COLOR.reset}`);
      } else if (ln.type === "error") {
        term.writeln(`${COLOR.error}[ERROR] ${ln.error}${COLOR.reset}`);
      } else if (ln.type === "user") {
        term.writeln(`${COLOR.bold}${COLOR.info}> ${ln.text}${COLOR.reset}`);
      }
    }
    writtenRef.current = lines.length;
  }, [lines]);

  return <div className="w-full h-full" ref={containerRef} data-testid="agent-terminal" />;
});

export default AgentTerminal;
