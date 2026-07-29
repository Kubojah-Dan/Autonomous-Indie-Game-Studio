import React from "react";

export default function TerminalWindow({ title, tone = "green", right, children, className = "", testId }) {
  const cls = tone === "cyan" ? "cyan" : tone === "magenta" ? "magenta" : "";
  return (
    <section className={`qf-window ${cls} ${className}`} data-testid={testId}>
      <div className="qf-title">
        <span className="flex items-center gap-2">
          <span className="dots"><span /><span /><span /></span>
          {title}
        </span>
        {right ? <span className="text-[10px] opacity-80">{right}</span> : null}
      </div>
      <div className="qf-body">{children}</div>
    </section>
  );
}
