"""
Output Renderer — converts raw skill JSON to human-readable Markdown.

No external template dependencies; uses only stdlib string operations.
"""
from __future__ import annotations

import json
from typing import Any

# ─── Public API ─────────────────────────────────────────────────────


def render_markdown(data: dict[str, Any]) -> str:
    """Convert a skill result dict to Markdown."""
    skill = data.get("skill", data.get("id", "Result"))
    success = data.get("success", data.get("ok", True))
    status_line = "✅ Success" if success else "❌ Failed"

    parts: list[str] = [f"# {skill} — {status_line}"]

    if message := data.get("message") or data.get("msg"):
        parts.append(f"\n{message}")

    parts.extend(_render_summary(data))
    parts.extend(_render_health(data))
    parts.extend(_render_items(data))
    parts.extend(_render_errors(data))

    return "\n\n".join(parts)


def render_html(data: dict[str, Any]) -> str:
    """Convert a skill result dict to simple HTML (Markdown wrapped in <div>)."""
    md = render_markdown(data)
    escaped = (
        md.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
    return f'<pre class="skill-output">{escaped}</pre>'


# ─── Section renderers ───────────────────────────────────────────────


def _render_summary(data: dict[str, Any]) -> list[str]:
    summary = data.get("summary") or data.get("stats")
    if not isinstance(summary, dict) or not summary:
        return []
    rows = "\n".join(
        f"| {_fmt_key(k)} | {v} |" for k, v in summary.items() if v is not None
    )
    return [f"## Summary\n\n| Metric | Value |\n|--------|-------|\n{rows}"]


def _render_health(data: dict[str, Any]) -> list[str]:
    parts: list[str] = []

    health_pct = (
        data.get("health_pct")
        or data.get("health")
        or (data.get("summary") or {}).get("health_pct")
    )
    if health_pct is not None:
        emoji = "🟢" if float(health_pct) >= 95 else "🟡" if float(health_pct) >= 75 else "🔴"
        parts.append(f"**Health:** {health_pct}% {emoji}")

    untested = data.get("untested") or (data.get("summary") or {}).get("untested")
    if untested:
        items = untested if isinstance(untested, list) else [untested]
        lines = "\n".join(f"- `{i}` — untested" for i in items)
        parts.append(f"## ⚠️ Items Needing Attention\n\n{lines}")

    broken = data.get("broken") or (data.get("summary") or {}).get("broken")
    if broken:
        items = broken if isinstance(broken, list) else [broken]
        lines = "\n".join(f"- `{i}` — **broken**" for i in items)
        parts.append(f"## ❌ Broken Items\n\n{lines}")

    return parts


def _render_items(data: dict[str, Any]) -> list[str]:
    items = data.get("items")
    if not items:
        return []
    if isinstance(items, list) and len(items) <= 20:
        lines = "\n".join(f"- {_fmt_item(i)}" for i in items)
        return [f"## Items\n\n{lines}"]
    if isinstance(items, dict):
        rows = "\n".join(
            f"| `{k}` | {_fmt_item(v)} |" for k, v in list(items.items())[:20]
        )
        return [f"## Items\n\n| Name | Status |\n|------|--------|\n{rows}"]
    return []


def _render_errors(data: dict[str, Any]) -> list[str]:
    err = data.get("error") or data.get("errors")
    if not err:
        return []
    if isinstance(err, list):
        lines = "\n".join(f"- {e}" for e in err)
        return [f"## Errors\n\n{lines}"]
    return [f"## Error\n\n```\n{err}\n```"]


# ─── Helpers ─────────────────────────────────────────────────────────


def _fmt_key(key: str) -> str:
    return key.replace("_", " ").title()


def _fmt_item(item: Any) -> str:
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        name = item.get("name") or item.get("id") or item.get("skill_id") or ""
        status = item.get("status") or item.get("state") or ""
        return f"`{name}` {status}".strip()
    return str(item)
