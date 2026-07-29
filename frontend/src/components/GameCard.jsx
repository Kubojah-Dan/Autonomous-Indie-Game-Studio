import React from "react";
import { Link } from "react-router-dom";

export default function GameCard({ game }) {
  const hue = (game.cover_seed || 0) % 360;
  const style = {
    filter: `hue-rotate(${hue}deg) saturate(1.05)`,
  };
  return (
    <Link
      to={`/play/${game.id}`}
      className="block group"
      data-testid={`vault-card-${game.id}`}
    >
      <div className="qf-cover" style={style}>
        <div className="absolute top-2 left-2 text-[10px] tracking-widest text-[color:var(--qf-cyan)]">
          [{game.id.slice(0, 8)}]
        </div>
        {game.demo && (
          <div className="absolute top-2 right-2 text-[10px] tracking-widest text-[color:var(--qf-magenta)] border border-[color:var(--qf-magenta)] px-1">
            PRE-FORGED
          </div>
        )}
        <div className="relative z-[1]">
          <div className="font-display text-2xl glow-green truncate group-hover:glow-cyan">
            {game.idea.slice(0, 48)}
          </div>
          <div className="text-[11px] text-[color:var(--qf-green)]/70 mt-1 uppercase tracking-widest">
            status :: {game.status}
          </div>
        </div>
      </div>
    </Link>
  );
}
