"""Writes generated game artifacts to disk and produces downloadable ZIPs."""
from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Dict

GENERATED_DIR = Path(os.getenv("GENERATED_GAMES_DIR", "/app/generated-games"))
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def write_game(game_id: str, idea: str, artifacts: Dict[str, str]) -> Path:
    root = GENERATED_DIR / game_id
    root.mkdir(parents=True, exist_ok=True)

    (root / "index.html").write_text(artifacts.get("code", ""), encoding="utf-8")
    (root / "CONCEPT.md").write_text(_concept_md(idea, artifacts), encoding="utf-8")
    (root / "manifest.json").write_text(json.dumps({
        "id": game_id,
        "idea": idea,
        "artifacts": list(artifacts.keys()),
    }, indent=2), encoding="utf-8")

    for key, content in artifacts.items():
        if key == "code":
            continue
        (root / f"{key}.md").write_text(str(content), encoding="utf-8")
    return root


def _concept_md(idea: str, a: Dict[str, str]) -> str:
    parts = [f"# QuantumForge :: {idea}\n"]
    order = ["plan", "concept", "references", "mechanics", "story",
             "sprite_prompts", "levels", "qa_report", "balance"]
    for k in order:
        if k in a:
            parts.append(f"\n## {k.upper()}\n\n{a[k]}\n")
    return "\n".join(parts)


def build_zip(game_id: str) -> bytes:
    root = GENERATED_DIR / game_id
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in root.rglob("*"):
            if p.is_file():
                zf.write(p, arcname=p.relative_to(root))
    return buf.getvalue()
