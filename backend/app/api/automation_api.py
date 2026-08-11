"""Automation API — surfaces the uDev automation engine.

GET  /api/automation/status     — engine config, git branch, pipeline state
POST /api/automation/run        — run the knowledge pipeline (body: {dry_run?, topic?})
GET  /api/automation/notebooks  — list generated .ipynb notebooks
POST /api/automation/research   — run a research question flow via OpenRouter
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from aiohttp import web

log = logging.getLogger("ucore.api.automation")

# Automation engine location (now in uCore services)
UDEV_DIR = Path(
    os.environ.get("UDEV_DIR", str(Path(__file__).resolve().parent.parent)),
)
ENGINE_DIR = UDEV_DIR / "services" / "automation"
ENGINE_SCRIPT = ENGINE_DIR / "engine.py"
KNOWLEDGE_ROOT = Path.home() / "Code" / "uDev" / "global-knowledge"


def _engine_exists() -> bool:
    return ENGINE_SCRIPT.exists()


async def _run_cmd(cmd: list[str], timeout: float = 120.0) -> tuple[int, str]:
    """Run a shell command asynchronously and capture output."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=str(ENGINE_DIR),
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        return proc.returncode or 0, out.decode(errors="replace")
    except asyncio.TimeoutError:
        proc.kill()
        return -1, "Command timed out"


def _git_branch() -> str:
    try:
        import subprocess

        res = subprocess.run(
            ["git", "-C", str(UDEV_DIR), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return res.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def _list_notebooks() -> list[dict]:
    if not KNOWLEDGE_ROOT.exists():
        return []
    notebooks = []
    for nb in sorted(KNOWLEDGE_ROOT.rglob("*.ipynb")):
        stat = nb.stat()
        notebooks.append(
            {
                "name": nb.name,
                "path": str(nb.relative_to(KNOWLEDGE_ROOT)),
                "size": stat.st_size,
                "mtime": stat.st_mtime,
            },
        )
    return notebooks


async def handle_status(request: web.Request) -> web.Response:
    """GET /api/automation/status"""
    engine = _engine_exists()
    notebooks = _list_notebooks()
    return web.json_response(
        {
            "engine": {
                "available": engine,
                "path": str(ENGINE_SCRIPT) if engine else None,
                "udev_dir": str(UDEV_DIR),
            },
            "git_branch": _git_branch(),
            "knowledge_root": str(KNOWLEDGE_ROOT),
            "notebook_count": len(notebooks),
            "notebooks": notebooks,
        },
    )


async def handle_run(request: web.Request) -> web.Response:
    """POST /api/automation/run"""
    if not _engine_exists():
        return web.json_response(
            {"error": f"Automation engine not found at {ENGINE_SCRIPT}"},
            status=404,
        )

    try:
        body = await request.json()
    except Exception:
        body = {}

    dry_run = bool(body.get("dry_run", False))
    topic = str(body.get("topic") or "").strip()

    cmd = ["python3", str(ENGINE_SCRIPT)]
    if dry_run:
        cmd.append("--dry-run")
    if topic:
        cmd += ["--topic", topic]

    code, output = await _run_cmd(cmd, timeout=180.0)
    return web.json_response(
        {
            "ok": code == 0,
            "exit_code": code,
            "dry_run": dry_run,
            "output": output[-4000:],
        },
        status=200 if code == 0 else 500,
    )


async def handle_notebooks(request: web.Request) -> web.Response:
    """GET /api/automation/notebooks"""
    return web.json_response({"notebooks": _list_notebooks()})


async def handle_notebook_markdown(request: web.Request) -> web.Response:
    """POST /api/automation/notebooks/markdown — convert a notebook to
    markdown for viewing in a markdown editor.

    Body: { path }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    rel_path = str(body.get("path") or "").strip()
    if not rel_path:
        return web.json_response({"error": "path is required"}, status=400)

    nb_path = (KNOWLEDGE_ROOT / rel_path).resolve()
    if not nb_path.exists() or nb_path.suffix.lower() != ".ipynb":
        return web.json_response(
            {"error": f"Notebook not found: {rel_path}"}, status=404,
        )

    try:
        markdown = _notebook_to_markdown(nb_path)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    return web.json_response(
        {
            "path": rel_path,
            "title": nb_path.stem.replace("-", " ").title(),
            "markdown": markdown,
        },
    )


# ── Notebook → Jekyll publishing ─────────────────────────────────

def _notebook_to_markdown(path: Path) -> str:
    """Convert a .ipynb notebook into markdown (cell by cell).

    Parses the notebook JSON directly (no nbformat dependency). Falls back
    to a naive text read if the JSON is malformed.
    """
    try:
        import nbformat

        nb = nbformat.read(str(path), as_version=4)
        parts: list[str] = []
        for cell in nb.cells:
            if cell.cell_type == "markdown":
                parts.append(_cell_source(cell))
            elif cell.cell_type == "code":
                source = _cell_source(cell)
                if not source.strip():
                    continue
                parts.append("```python\n" + source.strip("\n") + "\n```")
            elif cell.cell_type == "raw":
                parts.append(_cell_source(cell))
        return "\n\n".join(parts)
    except ImportError:
        log.warning("nbformat unavailable — parsing notebook JSON directly")
        return _notebook_to_markdown_json(path)
    except Exception as exc:
        raise ValueError(f"Failed to convert notebook: {exc}") from exc


def _cell_source(cell) -> str:
    src = getattr(cell, "source", "")
    if isinstance(src, list):
        return "".join(str(line) for line in src)
    return str(src)


def _notebook_to_markdown_json(path: Path) -> str:
    """Convert a .ipynb notebook to markdown by parsing the JSON directly."""
    import json as _json

    data = _json.loads(path.read_text(encoding="utf-8"))
    cells = data.get("cells", [])
    parts: list[str] = []
    for cell in cells:
        ctype = cell.get("cell_type", "")
        src = cell.get("source", [])
        if isinstance(src, list):
            src = "".join(str(line) for line in src)
        src = str(src)
        if ctype == "markdown":
            parts.append(src.strip("\n"))
        elif ctype == "code":
            if not src.strip():
                continue
            parts.append("```python\n" + src.strip("\n") + "\n```")
        elif ctype == "raw":
            parts.append(src.strip("\n"))
    return "\n\n".join(parts)


async def handle_publish_notebook(request: web.Request) -> web.Response:
    """POST /api/automation/notebooks/publish — convert a notebook and
    publish it as a Jekyll document via the standard publish flow.

    Body: { path, title?, collection?, publish_mode?, execute_git?, commit_message? }
    """
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    rel_path = str(body.get("path") or "").strip()
    if not rel_path:
        return web.json_response({"error": "path is required"}, status=400)

    nb_path = (KNOWLEDGE_ROOT / rel_path).resolve()
    if not nb_path.exists() or nb_path.suffix.lower() != ".ipynb":
        return web.json_response(
            {"error": f"Notebook not found: {rel_path}"}, status=404,
        )

    try:
        markdown_body = _notebook_to_markdown(nb_path)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    title = str(body.get("title") or nb_path.stem.replace("-", " ").title()).strip()
    # Reuse the canonical Jekyll publish flow with a notebook→markdown body.
    publish_body = {
        "content": markdown_body,
        "title": title,
        "slug": str(body.get("slug") or nb_path.stem),
        "collection": str(body.get("collection") or "posts"),
        "publish_mode": str(body.get("publish_mode") or "local"),
        "vault_layer": str(body.get("vault_layer") or "user"),
        "execute_git": bool(body.get("execute_git", False)),
        "commit_message": str(body.get("commit_message") or "").strip(),
        "tags": ["notebook", "automation"],
    }
    return await _publish_via_handler(publish_body)


async def _publish_via_handler(payload: dict) -> web.Response:
    """Call the Jekyll publish logic directly with a synthetic payload."""
    from datetime import UTC, datetime
    from pathlib import Path as P

    from app.api.user_workflow import (
        DEFAULT_USER_BINDER,
        VAULT_LAYERS,
        _jekyll_filename,
        _jekyll_target_dir,
        _render_import_document,
        _safe_binder_name,
        _safe_jekyll_collection,
        _safe_slug,
        _vault_layer_by_id,
    )

    content = str(payload.get("content") or "")
    title = str(payload.get("title") or "Untitled").strip() or "Untitled"
    slug = _safe_slug(str(payload.get("slug") or title))
    collection_raw = str(payload.get("collection") or "posts")
    publish_mode = str(payload.get("publish_mode") or "local").strip().lower()
    vault_layer_id = str(payload.get("vault_layer") or "public").strip()
    relative_dir = str(payload.get("relative_dir") or "").strip()
    binder = _safe_binder_name(str(payload.get("binder") or DEFAULT_USER_BINDER))
    execute_git = bool(payload.get("execute_git", False))
    commit_message = str(payload.get("commit_message") or "").strip()
    tags = payload.get("tags") or []

    layer = _vault_layer_by_id(vault_layer_id)
    if not layer:
        return web.json_response(
            {"error": f"Unknown vault_layer: {vault_layer_id}"}, status=400,
        )
    if str(layer.get("permissions") or "").lower() == "read_only":
        return web.json_response(
            {"error": f"vault_layer '{vault_layer_id}' is read-only"}, status=403,
        )

    try:
        collection = _safe_jekyll_collection(collection_raw)
        root = P(str(layer.get("path") or "")).expanduser()
        root.mkdir(parents=True, exist_ok=True)
        target_dir = _jekyll_target_dir(root, collection, relative_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        filename = _jekyll_filename(collection, slug)
        output_path = (target_dir / filename).resolve()
        if target_dir.resolve() not in output_path.parents:
            raise ValueError("Output path escapes target directory")

        frontmatter = {
            "layout": str(payload.get("layout") or "post"),
            "title": title,
            "date": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S +0000"),
            "tags": tags,
            "binder": binder,
            "workflow": "publish",
            "publish_mode": publish_mode,
            "source": "jupyter-notebook",
        }
        document = _render_import_document(frontmatter, content)
        output_path.write_text(document, encoding="utf-8")
        return web.json_response(
            {
                "ok": True,
                "path": str(output_path),
                "title": title,
                "source": "jupyter-notebook",
                "filename": filename,
                "collection": collection,
                "execute_git": execute_git,
            }
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    except Exception as exc:
        log.exception("Notebook Jekyll publish failed")
        return web.json_response(
            {"error": f"publish_notebook_jekyll_failed: {exc}"}, status=500,
        )


async def _llm_json(
    system: str,
    prompt: str,
    provider: str = "openrouter",
    model: str | None = None,
) -> dict | None:
    """Ask the provider router for a JSON object. Falls back to Ollama
    automatically (free local) when OpenRouter is unavailable."""
    try:
        from app.services.provider_router import get_provider_router

        router = get_provider_router()
        result = await router.chat(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            provider=provider,
            model=model,
            max_price=0.0,  # free tier only
        )
        text = str(result.get("text") or result.get("content") or "").strip()
        if not text and "message" in result:
            text = str(result["message"]).strip()
        if not text:
            return None
        # Extract the first JSON object from the response.
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return None
    except Exception as exc:
        log.warning("LLM research call failed: %s", exc)
        return None


async def handle_research_questions(request: web.Request) -> web.Response:
    """POST /api/automation/research/questions — generate research questions
    for a topic using the provider router (OpenRouter free → Ollama fallback)."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    topic = str(body.get("topic") or "").strip()
    if not topic:
        return web.json_response({"error": "topic is required"}, status=400)

    # Static fallback questions in case the LLM is unavailable.
    fallback = [
        {
            "id": "goals",
            "question": f"What do you want to achieve or understand about {topic}?",
            "options": ["Overview & fundamentals", "Practical implementation", "Comparative analysis", "Current state / trends"],
        },
        {
            "id": "audience",
            "question": "Who is this knowledge for, and at what depth?",
            "options": ["Beginners — accessible intro", "Practitioners — applied detail", "Experts — advanced nuances"],
        },
        {
            "id": "angle",
            "question": "What angle or lens should the research take?",
            "options": ["Technical deep-dive", "Best-practices guide", "Case studies & examples", "Conceptual overview"],
        },
        {
            "id": "sources",
            "question": "How many sources should be compiled?",
            "options": ["A few key sources (3-5)", "A broad set (6-12)", "Exhaustive survey (12+)"],
        },
    ]

    llm = await _llm_json(
        "You are a research planner. Generate 3-5 focused research questions for a given topic. "
        "Return ONLY a JSON array of objects, each with: id, question, options (array of 2-4 short option strings).",
        f"Topic: {topic}\nGenerate research questions.",
    )
    if isinstance(llm, list) and llm:
        return web.json_response({"topic": topic, "questions": llm, "source": "llm"})

    return web.json_response({"topic": topic, "questions": fallback, "source": "fallback"})


async def handle_research_generate(request: web.Request) -> web.Response:
    """POST /api/automation/research/generate — compile research answers into
    a knowledge document, write it to global-knowledge, and optionally publish
    to Jekyll."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON payload"}, status=400)

    topic = str(body.get("topic") or "").strip()
    if not topic:
        return web.json_response({"error": "topic is required"}, status=400)

    answers = body.get("answers") or {}
    if not isinstance(answers, dict):
        return web.json_response({"error": "answers must be an object"}, status=400)

    publish_jekyll = bool(body.get("publish", False))

    # Build a research markdown document.
    answers_text = "\n".join(
        f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in answers.items()
    )
    slug = (
        topic.lower()
        .replace(" ", "-")
        .replace("/", "-")
        .replace(":", "")
        .strip()
    )[:60] or "research"
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Optionally enrich via LLM.
    enriched = None
    llm = await _llm_json(
        "You are a research writer. Given a topic and answers, write a concise, "
        "well-structured markdown research summary (no frontmatter, no title heading). "
        "Return ONLY the markdown body.",
        f"Topic: {topic}\nAnswers:\n{answers_text}\n\nWrite the research summary.",
    )
    if isinstance(llm, dict) and llm.get("body"):
        enriched = str(llm["body"]).strip()

    body_md = enriched or (
        f"## Research: {topic}\n\n"
        f"**Date:** {today}\n\n"
        f"**Scope answers:**\n{answers_text}\n\n"
        f"_Draft generated from research questionnaire. Expand with sources via the automation pipeline._"
    )

    frontmatter = (
        "---\n"
        f'title: "{topic.replace(chr(34), chr(92) + chr(34))}"\n'
        f"date: {today}\n"
        "type: research\n"
        "status: draft\n"
        "tags: [research, automation]\n"
        "---\n\n"
    )
    document = frontmatter + body_md + "\n"

    # Write to global-knowledge/research/
    research_dir = KNOWLEDGE_ROOT / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    out_path = research_dir / f"{slug}.md"
    out_path.write_text(document, encoding="utf-8")

    result: dict = {
        "ok": True,
        "topic": topic,
        "path": str(out_path),
        "filename": out_path.name,
        "source": "llm" if enriched else "template",
        "content": document,
    }

    # Optionally publish to Jekyll.
    if publish_jekyll:
        publish_result = await _publish_via_handler(
            {
                "content": body_md,
                "title": topic,
                "slug": slug,
                "collection": "posts",
                "vault_layer": "user",
                "publish_mode": "local",
                "tags": ["research", "automation"],
            },
        )
        result["jekyll"] = publish_result

    return web.json_response(result)


def register_automation_routes(app: web.Application) -> None:
    """Register Automation API routes."""
    app.router.add_get("/api/automation/status", handle_status)
    app.router.add_post("/api/automation/run", handle_run)
    app.router.add_get("/api/automation/notebooks", handle_notebooks)
    app.router.add_post(
        "/api/automation/notebooks/markdown", handle_notebook_markdown,
    )
    app.router.add_post(
        "/api/automation/notebooks/publish", handle_publish_notebook,
    )
    app.router.add_post(
        "/api/automation/research/questions", handle_research_questions,
    )
    app.router.add_post(
        "/api/automation/research/generate", handle_research_generate,
    )
    log.debug("Automation API routes registered")
