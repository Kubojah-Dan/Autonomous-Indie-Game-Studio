import React, { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import axios from "axios";
import TerminalWindow from "@/components/TerminalWindow";
import ArtifactViewer from "@/components/ArtifactViewer";
import GamePreview from "@/components/GamePreview";

const BACKEND = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND}/api`;

export default function Play() {
  const { gameId } = useParams();
  const [meta, setMeta] = useState(null);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/game/${gameId}`);
        setMeta(r.data);
      } catch (e) {
        setErr(e?.response?.data?.detail || e.message);
      }
    })();
  }, [gameId]);

  if (err) {
    return (
      <div className="p-4">
        <TerminalWindow title={`[GAME :: ${gameId}]`} tone="magenta" testId="play-error">
          <div className="text-sm text-[color:var(--qf-magenta)]">// {err}</div>
          <Link to="/vault" className="qf-btn cyan mt-4 inline-block" data-testid="back-to-vault">Back to vault</Link>
        </TerminalWindow>
      </div>
    );
  }

  if (!meta) {
    return <div className="p-4 text-sm">// loading...</div>;
  }

  return (
    <div className="p-4 space-y-3">
      <TerminalWindow title={`[GAME :: ${meta.id}]`} right={meta.status} testId="play-meta">
        <div className="text-lg font-display glow-green">{meta.idea}</div>
        <div className="text-xs text-[color:var(--qf-cyan)] mt-1">forged {meta.created_at}</div>
      </TerminalWindow>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        <GamePreview gameId={meta.id} backendUrl={BACKEND} />
        <ArtifactViewer artifacts={meta.artifacts || {}} />
      </div>
    </div>
  );
}
