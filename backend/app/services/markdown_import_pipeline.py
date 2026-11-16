"""Markdown import pipeline for vault/binder ingestion.

Provides a single canonical conversion lane:
any supported input -> markdown -> vault/binder document.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from html.parser import HTMLParser
from typing import Any, Callable

import yaml

_INTAKE_FRONTMATTER = re.compile(r"^---[ \t]*\r?\n(.*?)^---[ \t]*(?:\r?\n|$)", re.M | re.S)


@dataclass(frozen=True)
class ConversionResult:
    markdown: str
    source_format: str
    plugin_id: str


def render_intake_markdown(
    markdown: str,
    metadata: dict[str, Any],
    *,
    source: str,
    source_kind: str,
    captured_at: str,
    payload: str,
    preserve_frontmatter: bool = False,
) -> str:
    """Render one frontmatter block while retaining authored metadata."""
    authored, markdown = _read_frontmatter(markdown) if preserve_frontmatter else ({}, markdown)

    frontmatter = {**metadata, **authored}
    for key in ("binder", "vault_layer"):
        if key in metadata:
            frontmatter[key] = metadata[key]
    if "intake" in authored:
        frontmatter["previous_intake"] = authored["intake"]
    frontmatter["intake"] = {
        "schema_version": 1,
        "source_kind": source_kind,
        "source": source,
        "captured_at": captured_at,
        "payload_sha256": hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    }
    front = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).rstrip()
    body = markdown.rstrip("\n") or "Imported document has no body."
    return f"---\n{front}\n---\n\n{body}\n"


def _read_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown or markdown.partition("\n")[0].rstrip() != "---":
        return {}, markdown
    match = _INTAKE_FRONTMATTER.match(markdown)
    if not match:
        raise ValueError("Unclosed Markdown frontmatter")
    try:
        parsed = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError("Invalid Markdown frontmatter") from exc
    if parsed is None:
        parsed = {}
    if not isinstance(parsed, dict):
        raise ValueError("Markdown frontmatter must be a mapping")
    return parsed, markdown[match.end():].lstrip("\r\n")


def check_intake_markdown(markdown: str) -> tuple[str, list[str]]:
    """Check provenance fields without claiming to verify the original payload."""
    try:
        metadata, _ = _read_frontmatter(markdown)
    except ValueError as exc:
        return "invalid", [str(exc)]
    if "intake" not in metadata:
        return "untracked", []
    intake = metadata["intake"]
    if not isinstance(intake, dict):
        return "invalid", ["Intake provenance must be a mapping."]
    issues = []
    if type(intake.get("schema_version")) is not int or intake["schema_version"] != 1:
        issues.append("Unsupported intake schema version.")
    if intake.get("source_kind") not in ("local", "web", "feed"):
        issues.append("Unrecognised source kind.")
    if not isinstance(intake.get("source"), str) or not intake["source"].strip():
        issues.append("Source is missing.")
    captured = intake.get("captured_at")
    try:
        if not isinstance(captured, str) or datetime.fromisoformat(captured).utcoffset() is None:
            raise ValueError
    except ValueError:
        issues.append("Capture time needs an ISO timestamp with a timezone.")
    digest = intake.get("payload_sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
        issues.append("Payload digest needs a SHA-256 value.")
    return ("invalid" if issues else "complete"), issues


class _HtmlToTextBridge(HTMLParser):
    """Lightweight HTML -> text bridge suitable for markdown imports."""

    _BLOCK_TAGS = {
        "p",
        "div",
        "section",
        "article",
        "header",
        "footer",
        "pre",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "ul",
        "ol",
        "li",
        "table",
        "tr",
    }

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._active_link: str | None = None

    def _append(self, text: str) -> None:
        if not text:
            return
        self.parts.append(text)

    def _newline(self) -> None:
        if self.parts and self.parts[-1].endswith("\n"):
            return
        self.parts.append("\n")

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        lowered = tag.lower()
        if lowered == "br":
            self._newline()
            return

        if lowered in self._BLOCK_TAGS:
            self._newline()

        if lowered == "li":
            self._append("- ")

        if lowered == "a":
            href = dict(attrs).get("href")
            self._active_link = href.strip() if href else None

    def handle_endtag(self, tag: str) -> None:
        lowered = tag.lower()
        if lowered == "a" and self._active_link:
            self._append(f" ({self._active_link})")
            self._active_link = None

        if lowered in self._BLOCK_TAGS:
            self._newline()

    def handle_data(self, data: str) -> None:
        text = unescape(data)
        if text:
            self._append(text)

    def to_text(self) -> str:
        text = "".join(self.parts)
        lines = [line.rstrip() for line in text.splitlines()]
        cleaned: list[str] = []
        previous_blank = False
        for line in lines:
            blank = not line.strip()
            if blank and previous_blank:
                continue
            cleaned.append(line)
            previous_blank = blank
        return "\n".join(cleaned).strip()


def _normalize_markdown(text: str) -> str:
    return text.strip() + "\n" if text.strip() else ""


def _convert_markdown(content: str) -> ConversionResult:
    return ConversionResult(
        markdown=content,
        source_format="markdown",
        plugin_id="builtin.markdown_passthrough",
    )


def _convert_text(content: str) -> ConversionResult:
    return ConversionResult(
        markdown=_normalize_markdown(content),
        source_format="text",
        plugin_id="builtin.text_passthrough",
    )


def _convert_html(content: str) -> ConversionResult:
    parser = _HtmlToTextBridge()
    parser.feed(content)
    parser.close()
    text = parser.to_text()
    return ConversionResult(
        markdown=_normalize_markdown(text),
        source_format="html",
        plugin_id="builtin.html_text_bridge",
    )


def _convert_json(content: str) -> ConversionResult:
    parsed = json.loads(content)
    pretty = json.dumps(parsed, indent=2, ensure_ascii=True)

    if isinstance(parsed, dict):
        keys = ", ".join(sorted(str(k) for k in parsed.keys()))
        header = f"Imported JSON object with keys: {keys}" if keys else "Imported JSON object"
    elif isinstance(parsed, list):
        header = f"Imported JSON list with {len(parsed)} item(s)."
    else:
        header = "Imported JSON value"

    markdown = "\n\n".join(
        [
            header,
            "```json\n" + pretty + "\n```",
        ],
    )
    return ConversionResult(
        markdown=_normalize_markdown(markdown),
        source_format="json",
        plugin_id="builtin.json_fenced",
    )


def _convert_unknown(content: str, declared_format: str) -> ConversionResult:
    language = re.sub(r"[^a-z0-9_-]+", "", declared_format.lower()) or "text"
    markdown = "\n\n".join(
        [
            f"Imported content from unsupported format: {declared_format}",
            f"```{language}\n{content}\n```",
        ],
    )
    return ConversionResult(
        markdown=_normalize_markdown(markdown),
        source_format=declared_format,
        plugin_id="builtin.fallback_fenced",
    )


_CONVERTERS: dict[str, Callable[[str], ConversionResult]] = {
    "markdown": _convert_markdown,
    "md": _convert_markdown,
    "text": _convert_text,
    "txt": _convert_text,
    "html": _convert_html,
    "json": _convert_json,
}


def detect_source_format(content: str) -> str:
    probe = (content or "").strip()
    if not probe:
        return "text"

    if probe.startswith("<") and ">" in probe:
        return "html"

    if probe[0] in "[{":
        try:
            json.loads(probe)
            return "json"
        except Exception:
            pass

    if _INTAKE_FRONTMATTER.match(content):
        return "markdown"

    markdown_markers = (
        "# ",
        "## ",
        "### ",
        "- ",
        "* ",
        "```",
        "[",
        "> ",
    )
    if any(probe.startswith(marker) for marker in markdown_markers):
        return "markdown"

    return "text"


def convert_content_to_markdown(
    content: str,
    source_format: str = "auto",
) -> ConversionResult:
    declared = (source_format or "auto").strip().lower()
    actual = detect_source_format(content) if declared in {"", "auto"} else declared

    converter = _CONVERTERS.get(actual)
    if converter is None:
        return _convert_unknown(content, actual)

    try:
        return converter(content)
    except Exception:
        if actual != "text":
            return _convert_text(content)
        raise
