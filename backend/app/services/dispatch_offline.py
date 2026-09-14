"""Sovereign Offline Dispatch & Capsule Exporter.

Builds 100% self-contained, single-file HTML dispatches ('story.standalone.html')
and portable signed '.capsule' archives.
Allows offline viewing from a USB flash drive without internet or server runtime.
Offline submissions download a formatted response JSON file for return to the host.
"""
from __future__ import annotations

import base64
import html
import json
import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.settings import settings
from app.services.dispatch_store import dispatch_store

log = logging.getLogger("ucore.dispatch_offline")


def generate_standalone_html(dispatch_id: str) -> str:
    """Generate self-contained single-file HTML story player."""
    dispatch = dispatch_store.get_dispatch(dispatch_id)
    if not dispatch:
        raise ValueError(f"Dispatch '{dispatch_id}' not found")

    manifest = dispatch["dispatch"]
    story_md = dispatch["story_markdown"]

    title = html.escape(manifest.get("title", "Sovereign Dispatch"))
    lead = html.escape(manifest.get("lead_text", ""))
    token = manifest.get("token", "")

    # Embed hero GIF as base64 data URI if available
    hero_b64 = ""
    dispatch_dir = dispatch_store.root_dir / dispatch_id
    hero_file = dispatch_dir / "originals" / "hero.gif"
    if hero_file.exists():
        hero_b64 = f"data:image/gif;base64,{base64.b64encode(hero_file.read_bytes()).decode('utf-8')}"
    elif manifest.get("hero_asset"):
        # Check catalog
        asset_name = Path(manifest["hero_asset"]).name
        catalog_file = settings.public_vault_root / "global-knowledge" / "elements" / asset_name
        if catalog_file.exists():
            hero_b64 = f"data:image/gif;base64,{base64.b64encode(catalog_file.read_bytes()).decode('utf-8')}"

    hero_img_tag = f'<img src="{hero_b64}" class="hero-img" alt="Hero Animation" />' if hero_b64 else ""

    # JSON escaped data for pure client-side runner
    escaped_story_json = json.dumps(story_md)
    escaped_manifest_json = json.dumps(manifest)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} — uDos Sovereign Story</title>
  <style>
    :root {{
      --bg: #0D1117;
      --card-bg: #161B22;
      --text-main: #E6EDF3;
      --text-muted: #8B949E;
      --border: #30363D;
      --accent: #58A6FF;
      --accent-hover: #79B8FF;
      --success: #3FB950;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text-main);
      font-family: Charter, 'Bitstream Charter', Cambria, Georgia, serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 24px 16px;
    }}
    .container {{
      width: 100%;
      max-width: 680px;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }}
    header {{
      text-align: center;
      padding: 16px 0;
    }}
    .hero-img {{
      width: 96px;
      height: 96px;
      border-radius: 8px;
      margin-bottom: 16px;
      image-rendering: pixelated;
    }}
    h1 {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 26px;
      font-weight: 700;
      color: var(--text-main);
      margin-bottom: 8px;
    }}
    .lead {{
      color: var(--text-muted);
      font-size: 16px;
      line-height: 1.5;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 28px 24px;
      font-size: 17px;
      line-height: 1.7;
    }}
    .card h2 {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 20px;
      margin-bottom: 12px;
      color: var(--accent);
    }}
    .card p {{ margin-bottom: 16px; }}
    .choice-item {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 14px;
      margin: 8px 0;
      border: 1px solid var(--border);
      border-radius: 6px;
      cursor: pointer;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 15px;
      transition: background 0.15s, border-color 0.15s;
    }}
    .choice-item:hover {{
      background: rgba(88, 166, 255, 0.08);
      border-color: var(--accent);
    }}
    .prompt-field {{
      margin: 14px 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    .prompt-field label {{
      display: block;
      font-size: 13px;
      color: var(--text-muted);
      margin-bottom: 6px;
    }}
    .prompt-field input {{
      width: 100%;
      padding: 10px 12px;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-main);
      font-size: 15px;
    }}
    .prompt-field input:focus {{
      outline: none;
      border-color: var(--accent);
    }}
    .actions {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-top: 20px;
    }}
    button {{
      background: var(--accent);
      color: var(--bg);
      border: none;
      border-radius: 6px;
      padding: 10px 20px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-weight: 600;
      font-size: 15px;
      cursor: pointer;
      transition: background 0.15s;
    }}
    button:hover {{ background: var(--accent-hover); }}
    button:disabled {{ opacity: 0.5; cursor: not-allowed; }}
    footer {{
      text-align: center;
      color: var(--text-muted);
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      font-size: 12px;
      padding: 24px 0;
    }}
    .success-box {{
      background: rgba(63, 185, 80, 0.12);
      border: 1px solid var(--success);
      color: var(--text-main);
      padding: 20px;
      border-radius: 8px;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      {hero_img_tag}
      <h1>{title}</h1>
      <p class="lead">{lead}</p>
    </header>

    <main id="app-content">
      <div class="card" id="card-display">
        <!-- Rendered dynamically -->
      </div>
    </main>

    <footer>
      Dispatched via sovereign uDos • 100% Offline • Zero Tracking Pixels
    </footer>
  </div>

  <script>
    const storyRaw = {escaped_story_json};
    const manifest = {escaped_manifest_json};
    const token = "{token}";

    // Split markdown cards by '---'
    const cards = storyRaw.split(/\\n\\s*---\\s*\\n/).map(c => c.trim()).filter(Boolean);
    let currentCardIdx = 0;
    const userAnswers = {{}};

    function parseCard(md) {{
      let htmlContent = "";
      const lines = md.split('\\n');
      for (let line of lines) {{
        line = line.trim();
        if (line.startsWith('# ')) {{
          htmlContent += '<h1>' + line.slice(2) + '</h1>';
        }} else if (line.startsWith('## ')) {{
          htmlContent += '<h2>' + line.slice(3) + '</h2>';
        }} else if (line.startsWith('? [ ] ')) {{
          const choiceText = line.slice(6);
          const checked = userAnswers[choiceText] ? 'checked' : '';
          htmlContent += `<div class="choice-item" onclick="toggleChoice('${{choiceText}}')">
            <input type="checkbox" id="c_${{choiceText}}" ${{checked}} />
            <label>${{choiceText}}</label>
          </div>`;
        }} else if (line.startsWith('? (') && line.includes('): [text]')) {{
          const label = line.substring(3, line.indexOf('): [text]'));
          const val = userAnswers[label] || '';
          htmlContent += `<div class="prompt-field">
            <label>${{label}}</label>
            <input type="text" value="${{val}}" oninput="recordPrompt('${{label}}', this.value)" />
          </div>`;
        }} else if (line.length > 0) {{
          htmlContent += '<p>' + line + '</p>';
        }}
      }}
      return htmlContent;
    }}

    function render() {{
      const display = document.getElementById("card-display");
      if (currentCardIdx >= cards.length) {{
        // Complete & download response
        display.innerHTML = `
          <div class="success-box">
            <h2>Thank You for Responding Peacefully</h2>
            <p>Your responses have been recorded in this offline dispatch.</p>
            <button onclick="downloadResponse()">Download response-${{token.slice(0, 8)}}.json</button>
          </div>
        `;
        return;
      }}

      const cardHtml = parseCard(cards[currentCardIdx]);
      const isLast = currentCardIdx === cards.length - 1;
      const nextBtnLabel = isLast ? "Submit & Save Response" : "Next Step →";

      display.innerHTML = `
        ${{cardHtml}}
        <div class="actions">
          <span style="font-size: 13px; color: var(--text-muted);">Step ${{currentCardIdx + 1}} of ${{cards.length}}</span>
          <button onclick="nextStep()">${{nextBtnLabel}}</button>
        </div>
      `;
    }}

    function toggleChoice(key) {{
      userAnswers[key] = !userAnswers[key];
      render();
    }}

    function recordPrompt(key, val) {{
      userAnswers[key] = val;
    }}

    function nextStep() {{
      currentCardIdx++;
      render();
    }}

    function downloadResponse() {{
      const payload = {{
        token: token,
        dispatch_id: manifest.id,
        timestamp: Math.floor(Date.now() / 1000),
        answers: userAnswers
      }};
      const blob = new Blob([JSON.stringify(payload, null, 2)], {{ type: 'application/json' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `response-${{token.slice(0, 8)}}.json`;
      a.click();
      URL.revokeObjectURL(url);
    }}

    // Initial render
    render();
  </script>
</body>
</html>"""


def export_offline_bundle(dispatch_id: str) -> Dict[str, Any]:
    """Generate standalone HTML and pack into a signed .capsule archive."""
    html_content = generate_standalone_html(dispatch_id)

    invites_dir = settings.shared_vault_root / "invites"
    capsules_dir = settings.shared_vault_root / "capsules"
    invites_dir.mkdir(parents=True, exist_ok=True)
    capsules_dir.mkdir(parents=True, exist_ok=True)

    html_path = invites_dir / f"{dispatch_id}.html"
    html_path.write_text(html_content, encoding="utf-8")

    # Also prepare a directory bundle for capsule packaging
    dispatch_dir = dispatch_store.root_dir / dispatch_id
    capsule_out = capsules_dir / f"{dispatch_id}.capsule"

    # Attempt to pack with sonic CLI or python
    try:
        sonic_venv = Path(__file__).resolve().parents[4] / "SonicScrewdriver" / ".venv" / "bin" / "sonic"
        if sonic_venv.exists():
            cmd = [
                str(sonic_venv),
                "package", "pack",
                str(dispatch_dir),
                "--out", str(capsule_out),
                "--title", f"Dispatch {dispatch_id}",
            ]
            subprocess.run(cmd, capture_output=True, check=True)
    except Exception as exc:
        log.warning("Could not pack with sonic CLI: %s. Writing standalone HTML only.", exc)

    return {
        "status": "ok",
        "dispatch_id": dispatch_id,
        "standalone_html_path": str(html_path),
        "capsule_path": str(capsule_out) if capsule_out.exists() else None,
    }
