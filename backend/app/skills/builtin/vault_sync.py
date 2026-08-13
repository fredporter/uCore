"""vault_sync — Rebuild the unified vault library index.

Scans ~/Vault (master user vault), ~/Shared, and ~/Public into the
FTS5 index at ~/.ucore/indices/library.db, then reports per-source
file counts.

Usage:
  POST /api/skills/vault_sync/run
  Body: { "dry_run": false, "summary_only": true }
"""
from __future__ import annotations

from app.services import library_index
from app.skills.base import BaseSkill, SkillMeta, SkillParam


class VaultSync(BaseSkill):
    meta = SkillMeta(
        id="vault_sync",
        name="Vault Sync",
        description="Rebuild the vault library index from ~/Vault, ~/Shared, and ~/Public",
        category="maintenance",
        timeout=300,
        params=[
            SkillParam(
                name="dry_run",
                type="boolean",
                required=False,
                default=False,
                description="Only report the vault roots without rebuilding",
            ),
            SkillParam(
                name="summary_only",
                type="boolean",
                required=False,
                default=True,
                description="Return condensed per-source counts",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        dry_run = bool(kwargs.get("dry_run", False))
        summary_only = bool(kwargs.get("summary_only", True))

        if dry_run:
            return {
                "success": True,
                "status": "dry-run",
                "dry_run": True,
                "sources": [
                    {"source": key, "path": str(path)}
                    for key, path in library_index.VAULT_PATHS.items()
                ],
            }

        result = library_index.build_index()
        if summary_only:
            sources = result.get("sources", [])
            return {
                "success": True,
                "status": "ok",
                "total_indexed": result.get("total_indexed", 0),
                "sources": [
                    {
                        "source": s.get("source"),
                        "files": s.get("files", 0),
                        "status": s.get("status"),
                    }
                    for s in sources
                ],
            }
        return {"success": True, "status": "ok", **result}
