import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route, Link, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import "@/App.css";

import BootSequence from "@/components/BootSequence";
import Studio from "@/pages/Studio";
import Vault from "@/pages/Vault";
import Play from "@/pages/Play";

const ASCII = `  ___  _   _  _   _ _____ _   _ __  __ _____ ___  ___   ___ ___
 / _ \\| | | || \\ | |_   _| | | |  \\/  |  ___/ _ \\| _ \\ / __| __|
| | | | | | ||  \\| | | | | |_| | |\\/| | |_ | | | |   /| |  | _|
| |_| | |_| || |\\  | | | |  _  | |  | |  _|| |_| | |\\ \\| |__| |__
 \\__\\_\\\\___/ |_| \\_| |_| |_| |_|_|  |_|_|   \\___/|_| \\_\\\\___|____|`;

function TopBar() {
  const loc = useLocation();
  const link = (to, label) => (
    <Link
      to={to}
      data-testid={`nav-${label.toLowerCase()}`}
      className={`qf-glitch font-display text-xl px-3 py-1 border ${loc.pathname === to ? "bg-[color:var(--qf-green)] text-[color:var(--qf-bg)]" : "border-[color:var(--qf-green)] text-[color:var(--qf-green)]"} `}
      data-text={label}
    >
      {label}
    </Link>
  );
  return (
    <header className="px-4 pt-3 pb-2 border-b border-[color:var(--qf-green)]/40 flex flex-col md:flex-row md:items-end md:justify-between gap-3">
      <div>
        <pre className="qf-ascii glow-green" aria-hidden>{ASCII}</pre>
        <div className="mt-1 flex items-baseline gap-3 flex-wrap">
          <span className="font-display text-2xl glow-green">[QUANTUMFORGE::v1.0]</span>
          <span className="text-xs uppercase tracking-widest text-[color:var(--qf-cyan)]">Autonomous Indie Game Dev Studio</span>
          <span className="qf-cursor" />
        </div>
      </div>
      <nav className="flex gap-2 items-center" data-testid="top-nav">
        {link("/", "Studio")}
        {link("/vault", "Vault")}
        <a
          href="https://github.com/topics/phaser"
          target="_blank"
          rel="noreferrer"
          className="qf-glitch font-display text-xl px-3 py-1 border border-[color:var(--qf-cyan)] text-[color:var(--qf-cyan)]"
          data-text="DOCS"
          data-testid="nav-docs"
        >
          DOCS
        </a>
      </nav>
    </header>
  );
}

function Shell({ children }) {
  return (
    <div className="min-h-screen relative">
      <div className="crt-vignette" />
      <div className="crt-scanlines" />
      <TopBar />
      <main className="relative z-[1]">{children}</main>
      <Toaster
        position="top-right"
        toastOptions={{ unstyled: true, classNames: { toast: "qf-achievement", title: "font-display" } }}
      />
    </div>
  );
}

export default function App() {
  const [booted, setBooted] = useState(() => sessionStorage.getItem("qf-booted") === "1");

  useEffect(() => {
    if (booted) sessionStorage.setItem("qf-booted", "1");
  }, [booted]);

  return (
    <BrowserRouter>
      {!booted && <BootSequence onDone={() => setBooted(true)} />}
      <Shell>
        <Routes>
          <Route path="/" element={<Studio />} />
          <Route path="/vault" element={<Vault />} />
          <Route path="/play/:gameId" element={<Play />} />
        </Routes>
      </Shell>
    </BrowserRouter>
  );
}
