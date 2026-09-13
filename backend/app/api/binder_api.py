"""Binder API — Durable Binder Engine & Intake REST Endpoints.

Provides complete REST lifecycle for notebook binders:
- GET    /api/binder/list           — list all binders with metadata
- POST   /api/binder/create         — create a durable notebook binder (also aliased to /api/binder/add)
- GET    /api/binder/{binder_id}    — retrieve binder record package (brief, requirements, sources, draft, evidence, editions)
- POST   /api/binder/{binder_id}/intake — intake source document into vault & attach to binder
- POST   /api/binder/{binder_id}/run    — execute uFlow bounded assembly run
- PATCH  /api/binder/{binder_id}/draft  — update draft with concurrency conflict detection (base_hash)
- POST   /api/binder/{binder_id}/accept — freeze current draft into immutable edition snapshot
- POST   /api/binder/{binder_id}/publish — compile accepted edition into offline static bundle
- PATCH  /api/binder/update         — legacy metadata update
- PATCH  /api/binder/score          — legacy score update
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aiohttp import web

from app.flow import binder_engine
from app.flow.binder_engine import ConcurrencyConflictError
from app.services import intake_service

log = logging.getLogger("ucore.binder_api")

VAULT_ROOT = Path.home() / "Vault"


def _legacy_binder_path(binder_name: str) -> Path:
    return VAULT_ROOT / binder_name.strip().replace("/", "-")


def _legacy_meta_path(binder_name: str) -> Path:
    return _legacy_binder_path(binder_name) / "binder.json"


def _load_legacy_meta(binder_name: str) -> dict:
    mp = _legacy_meta_path(binder_name)
    if mp.exists():
        try:
            return json.loads(mp.read_text())
        except Exception:
            pass
    return {
        "name": binder_name,
        "description": "",
        "created": datetime.now(UTC).isoformat(),
        "updated": datetime.now(UTC).isoformat(),
        "score": 0,
        "tags": [],
        "sources": [],
    }


def _save_legacy_meta(binder_name: str, meta: dict) -> None:
    mp = _legacy_meta_path(binder_name)
    mp.parent.mkdir(parents=True, exist_ok=True)
    meta["updated"] = datetime.now(UTC).isoformat()
    mp.write_text(json.dumps(meta, indent=2))


async def handle_binder_list(request: web.Request) -> web.Response:
    """GET /api/binder/list — list all binders."""
    try:
        binders = binder_engine.list_binders()
    except Exception as e:
        log.warning("Failed listing binders from binder_engine: %s", e)
        binders = []

    # Also include any legacy root binders not in Binders/
    seen_names = {b.get("id", b.get("name")) for b in binders}
    if VAULT_ROOT.exists():
        for d in sorted(VAULT_ROOT.iterdir()):
            if d.is_dir() and d.name not in ("Binders", "Originals", "Documents") and (d / "binder.json").exists():
                if d.name not in seen_names:
                    try:
                        legacy = _load_legacy_meta(d.name)
                        binders.append(legacy)
                    except Exception:
                        pass

    return web.json_response({"binders": binders, "count": len(binders)})


async def handle_binder_create(request: web.Request) -> web.Response:
    """POST /api/binder/create (or /api/binder/add) — create a new durable binder."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    binder_id = body.get("id") or body.get("name")
    if not binder_id or not str(binder_id).strip():
        return web.json_response({"error": "id or name is required"}, status=400)

    binder_id = str(binder_id).strip()
    title = body.get("title") or binder_id
    outcome = body.get("outcome") or body.get("description") or f"Production binder for {title}"
    audience = body.get("audience", "General")
    doc_type = body.get("document_type", "Document")
    reqs = body.get("requirements")
    non_goals = body.get("non_goals")

    try:
        created = binder_engine.create_binder(
            binder_id=binder_id,
            title=title,
            outcome=outcome,
            audience=audience,
            document_type=doc_type,
            requirements=reqs,
            non_goals=non_goals,
        )
        return web.json_response({"created": True, "binder": created})
    except FileExistsError:
        return web.json_response({"error": f"Binder '{binder_id}' already exists"}, status=409)
    except Exception as e:
        log.exception("Error creating binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_add(request: web.Request) -> web.Response:
    """POST /api/binder/add — alias to create for backward compatibility."""
    return await handle_binder_create(request)


async def handle_binder_get(request: web.Request) -> web.Response:
    """GET /api/binder/{binder_id} — get full durable binder records."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        data = binder_engine.get_binder(binder_id)
        return web.json_response({"binder": data})
    except FileNotFoundError:
        # Check legacy path
        legacy_meta = _legacy_meta_path(binder_id)
        if legacy_meta.exists():
            meta = _load_legacy_meta(binder_id)
            return web.json_response({
                "binder": {
                    "metadata": meta,
                    "brief": meta.get("description", ""),
                    "draft": "",
                    "requirements": [],
                    "sources": meta.get("sources", []),
                    "plan": [],
                    "evidence": [],
                    "editions": [],
                }
            })
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error loading binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_intake(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/intake — ingest original document and attach as source."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    file_name = ""
    content_bytes = b""
    author = "Unknown"
    source_uri = ""

    if request.content_type.startswith("multipart/"):
        reader = await request.multipart()
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "file":
                file_name = part.filename or "document.bin"
                content_bytes = await part.read()
            elif part.name == "author":
                author = (await part.text()).strip()
            elif part.name == "source_uri":
                source_uri = (await part.text()).strip()
    else:
        try:
            body = await request.json()
        except Exception:
            return web.json_response({"error": "Invalid payload format"}, status=400)

        file_name = body.get("file_name", "document.md")
        author = body.get("author", "Unknown")
        source_uri = body.get("source_uri", "")

        raw_content = body.get("content", "")
        if body.get("is_base64"):
            try:
                content_bytes = base64.b64decode(raw_content)
            except Exception:
                return web.json_response({"error": "Invalid base64 content"}, status=400)
        else:
            content_bytes = raw_content.encode("utf-8")

    if not content_bytes:
        return web.json_response({"error": "No file content provided for intake"}, status=400)

    try:
        bdir = binder_engine._binder_dir(binder_id)
        if bdir.exists():
            receipt = intake_service.intake_binder_source(
                binder_dir=bdir,
                file_name=file_name,
                content_bytes=content_bytes,
                source_uri=source_uri,
                author=author,
            )
        else:
            receipt = intake_service.intake_file(
                file_name=file_name,
                content_bytes=content_bytes,
                source_uri=source_uri,
                author=author,
            )

        source_entry = binder_engine.attach_source_to_binder(
            binder_id=binder_id,
            doc_id=receipt["doc_id"],
            file_name=receipt["file_name"],
            source_sha256=receipt["source_sha256"],
            markdown_path=receipt["markdown_path"],
            original_path=receipt.get("original_path"),
        )

        return web.json_response({
            "success": True,
            "receipt": receipt,
            "source": source_entry,
        })
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error processing intake for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_run(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/run — execute bounded uFlow assembly run."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        updated = binder_engine.assemble_draft(binder_id)
        return web.json_response({"success": True, "binder": updated})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error running assembly for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_draft_update(request: web.Request) -> web.Response:
    """PATCH /api/binder/{binder_id}/draft — update draft with concurrency conflict detection."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    content = body.get("content")
    if content is None:
        return web.json_response({"error": "content required"}, status=400)

    expected_base_hash = body.get("expected_base_hash")

    try:
        res = binder_engine.update_draft(binder_id, content, expected_base_hash)
        return web.json_response({"success": True, **res})
    except ConcurrencyConflictError as cce:
        return web.json_response({"error": "concurrency_conflict", "message": str(cce)}, status=409)
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error updating draft for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_accept(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/accept — accept draft into an immutable edition snapshot."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        body = {}

    notes = body.get("notes", "")

    try:
        manifest = binder_engine.accept_edition(binder_id, reviewer_notes=notes)
        return web.json_response({"accepted": True, "edition": manifest})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error accepting edition for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_publish(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/publish — compile accepted edition into offline static bundle."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        body = {}

    edition_num = body.get("edition")
    target = body.get("target", "local_static")

    try:
        receipt = binder_engine.publish_edition(binder_id, edition_num=edition_num, target=target)
        return web.json_response({"published": True, "receipt": receipt})
    except (FileNotFoundError, ValueError) as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.exception("Error publishing edition for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_update(request: web.Request) -> web.Response:
    """PATCH /api/binder/update — update legacy binder metadata."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    name = body.get("name", "").strip()
    if not name:
        return web.json_response({"error": "name required"}, status=400)
    mp = _legacy_meta_path(name)
    if not mp.exists():
        return web.json_response({"error": "Binder not found"}, status=404)
    meta = _load_legacy_meta(name)
    for key in ("description", "tags", "sources", "score"):
        if key in body:
            meta[key] = body[key]
    _save_legacy_meta(name, meta)
    return web.json_response({"updated": True, "binder": meta})


async def handle_binder_score(request: web.Request) -> web.Response:
    """PATCH /api/binder/score — set quality score (0-5)."""
    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    name = body.get("name", "").strip()
    score = body.get("score", 0)
    if not name:
        return web.json_response({"error": "name required"}, status=400)
    score = max(0, min(5, int(score)))
    mp = _legacy_meta_path(name)
    if not mp.exists():
        return web.json_response({"error": "Binder not found"}, status=404)
    meta = _load_legacy_meta(name)
    meta["score"] = score
    _save_legacy_meta(name, meta)
    return web.json_response({"scored": True, "score": score, "binder": meta})


async def handle_binder_authorise(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/authorise — authorize bounded execution run."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        body = {}

    run_budget = body.get("run_budget")
    network_allowed = bool(body.get("network_allowed", False))

    try:
        receipt = binder_engine.authorise_run(
            binder_id=binder_id,
            run_budget=run_budget,
            network_allowed=network_allowed,
        )
        return web.json_response({"authorised": True, "receipt": receipt})
    except (FileNotFoundError, ValueError) as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.exception("Error authorising run for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_resume(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/resume — resume run from checkpoint."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        updated = binder_engine.resume_or_reconcile_run(binder_id)
        return web.json_response({"success": True, "binder": updated})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error resuming run for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_audit(request: web.Request) -> web.Response:
    """GET /api/binder/{binder_id}/audit — run deterministic anti-drift audit."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        result = binder_engine.audit_binder(binder_id)
        return web.json_response({"audit": result})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error auditing binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_decisions_get(request: web.Request) -> web.Response:
    """GET /api/binder/{binder_id}/decisions — list recorded decisions."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        decisions = binder_engine.list_decisions(binder_id)
        return web.json_response({"decisions": decisions})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_decisions_post(request: web.Request) -> web.Response:
    """POST /api/binder/{binder_id}/decisions — record a decision."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    title = body.get("title", "").strip()
    if not title:
        return web.json_response({"error": "title required"}, status=400)

    status = body.get("status", "accepted")
    rationale = body.get("rationale", "")
    superseded_by = body.get("superseded_by")

    try:
        entry = binder_engine.record_decision(
            binder_id=binder_id,
            title=title,
            status=status,
            rationale=rationale,
            superseded_by=superseded_by,
        )
        return web.json_response({"success": True, "decision": entry})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error recording decision for binder %s: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_section_update(request: web.Request) -> web.Response:
    """PATCH /api/binder/{binder_id}/section/{req_id} — targeted section update."""
    binder_id = request.match_info.get("binder_id", "").strip()
    req_id = request.match_info.get("req_id", "").strip()
    if not binder_id or not req_id:
        return web.json_response({"error": "binder_id and req_id required"}, status=400)

    try:
        body = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON"}, status=400)

    content = body.get("content")
    if content is None:
        return web.json_response({"error": "content required"}, status=400)

    expected_hash = body.get("expected_section_hash")

    try:
        res = binder_engine.update_section(
            binder_id=binder_id,
            req_id=req_id,
            new_section_body=content,
            expected_section_hash=expected_hash,
        )
        return web.json_response({"success": True, **res})
    except ConcurrencyConflictError as cce:
        return web.json_response({"error": "concurrency_conflict", "message": str(cce)}, status=409)
    except (FileNotFoundError, ValueError) as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        log.exception("Error updating section %s for binder %s: %s", req_id, binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_export_gemini(request: web.Request) -> web.Response:
    """GET /api/binder/{binder_id}/export/gemini — export for Gemini NotebookLM."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        package = binder_engine.export_gemini_notebook(binder_id)
        return web.json_response({"success": True, "package": package})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error exporting binder %s for Gemini: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)


async def handle_binder_export_obsidian(request: web.Request) -> web.Response:
    """GET /api/binder/{binder_id}/export/obsidian — export Obsidian index."""
    binder_id = request.match_info.get("binder_id", "").strip()
    if not binder_id:
        return web.json_response({"error": "binder_id required"}, status=400)

    try:
        res = binder_engine.export_obsidian_binder(binder_id)
        return web.json_response({"success": True, **res})
    except FileNotFoundError:
        return web.json_response({"error": f"Binder '{binder_id}' not found"}, status=404)
    except Exception as e:
        log.exception("Error exporting binder %s for Obsidian: %s", binder_id, e)
        return web.json_response({"error": str(e)}, status=500)
