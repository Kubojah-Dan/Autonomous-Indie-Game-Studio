import React from "react";
import TerminalWindow from "@/components/TerminalWindow";

export default function GamePreview({ gameId, backendUrl }) {
  if (!gameId) {
    return (
      <TerminalWindow title="[PLAYABLE PROTOTYPE]" tone="magenta" testId="preview-empty">
        <div className="text-sm text-[color:var(--qf-green)]/70">
          <span className="glow-magenta">// no build available yet</span>
        </div>
      </TerminalWindow>
    );
  }
  const src = `${backendUrl}/api/game/${gameId}/play`;
  return (
    <TerminalWindow title={`[PLAYABLE PROTOTYPE :: ${gameId}]`} tone="magenta" right="800x600" testId="preview-window">
      <div className="w-full flex justify-center">
        <iframe
          title={`play-${gameId}`}
          src={src}
          width={800}
          height={600}
          className="border border-[color:var(--qf-magenta)]/60 bg-[color:var(--qf-bg)]"
          data-testid="game-iframe"
          allow="autoplay; fullscreen"
          sandbox="allow-scripts allow-same-origin"
        />
      </div>
      <div className="flex gap-2 mt-3 justify-end">
        <a
          className="qf-btn magenta"
          href={`${backendUrl}/api/game/${gameId}/download`}
          data-testid="download-game-button"
        >
          Download .zip
        </a>
        <a
          className="qf-btn cyan"
          href={src}
          target="_blank"
          rel="noreferrer"
          data-testid="open-fullscreen-button"
        >
          Open Fullscreen
        </a>
      </div>
    </TerminalWindow>
  );
}
