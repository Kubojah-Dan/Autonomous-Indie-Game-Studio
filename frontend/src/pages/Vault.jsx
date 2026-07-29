import React, { useEffect, useState } from "react";
import axios from "axios";
import GameCard from "@/components/GameCard";
import TerminalWindow from "@/components/TerminalWindow";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function Vault() {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        const r = await axios.get(`${API}/vault`);
        setGames(r.data.games || []);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  return (
    <div className="p-4">
      <TerminalWindow title="[PROJECT VAULT]" right={`${games.length} entries`} testId="vault-window">
        {loading && <div className="text-sm text-[color:var(--qf-green)]/70">// scanning vault...</div>}
        {!loading && games.length === 0 && (
          <div className="text-sm text-[color:var(--qf-green)]/70" data-testid="vault-empty">
            // no games forged yet. head back to the Studio and forge one.
          </div>
        )}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4" data-testid="vault-grid">
          {games.map((g) => (
            <GameCard key={g.id} game={g} />
          ))}
        </div>
      </TerminalWindow>
    </div>
  );
}
