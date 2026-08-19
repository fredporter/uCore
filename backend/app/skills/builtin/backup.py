"""backup — Comprehensive backup skill with retention management.

Supports both manual and scheduled (daily) backups with selective
component backup and automatic old-backup cleanup.

Usage:
  POST /api/skills/backup/run
  Body: {
    "type": "full" | "database" | "config" | "secrets" | "wisdom",
    "destination": "$UDOS_HOME/backups",
    "retention_days": 14
  }
"""

from __future__ import annotations

import logging
import shutil
import tarfile
import time
from datetime import datetime
from pathlib import Path

from app.core.logging import log
from app.core.settings import settings
from app.services.wisdom_paths import readable_wisdom_path
from app.skills.base import BaseSkill, SkillMeta, SkillParam

RETENTION_DAYS = 14


class BackupData(BaseSkill):
    meta = SkillMeta(
        id="backup",
        name="Backup Data",
        description=(
            "Backup uCore database, config, secrets, private wisdom, "
            "and user data with retention management"
        ),
        category="maintenance",
        timeout=120,
        params=[
            SkillParam(
                name="type",
                type="string",
                required=False,
                default="full",
                description="Backup type: full, database, config, secrets, wisdom",
            ),
            SkillParam(
                name="destination",
                type="string",
                required=False,
                default=str(settings.udos_home / "backups"),
            ),
            SkillParam(
                name="retention_days",
                type="integer",
                required=False,
                default=RETENTION_DAYS,
                description="Days to retain backups before cleanup",
            ),
        ],
        requires_confirmation=True,
    )

    async def run(self, **kwargs) -> dict:
        backup_type = kwargs.get("type", "full").strip().lower()
        dest = Path(
            kwargs.get("destination", str(settings.udos_home / "backups")),
        ).expanduser()
        dest.mkdir(parents=True, exist_ok=True)
        retention_days = kwargs.get("retention_days", RETENTION_DAYS)
        ts = time.strftime("%Y%m%d-%H%M%S")

        backup_entries = []

        # 1. Database
        if backup_type in ("full", "database"):
            entry = self._backup_database(dest, ts)
            if entry:
                backup_entries.append(entry)

        # 2. Private project wisdom
        if backup_type in ("full", "wisdom"):
            entry = self._backup_wisdom(dest, ts)
            if entry:
                backup_entries.append(entry)

        # 3. Secrets
        if backup_type in ("full", "secrets"):
            entry = self._backup_secrets(dest, ts)
            if entry:
                backup_entries.append(entry)

        # 4. Config
        if backup_type in ("full", "config"):
            entry = self._backup_config(dest, ts)
            if entry:
                backup_entries.append(entry)

        # 5. Cleanup old backups
        removed = self._cleanup_old_backups(dest, retention_days)

        log.info(
            "Backup completed: %d files backed up to %s (%d old removed)",
            len(backup_entries),
            dest,
            removed,
        )
        return {
            "success": True,
            "backup_dir": str(dest),
            "type": backup_type,
            "files": backup_entries,
            "count": len(backup_entries),
            "old_backups_removed": removed,
        }

    def _backup_database(self, dest: Path, ts: str) -> dict | None:
        """Backup the SQLite database."""
        from app.core.database import get_db_path

        db_path = get_db_path()
        if db_path and Path(db_path).exists():
            backup_file = dest / f"ucore-backup-{ts}.db"
            shutil.copy2(db_path, backup_file)
            return {
                "component": "database",
                "file": str(backup_file),
                "size": backup_file.stat().st_size,
            }
        return None

    def _backup_wisdom(self, dest: Path, ts: str) -> dict | None:
        """Backup private project wisdom."""
        wisdom_path = readable_wisdom_path()
        if wisdom_path.exists():
            wisdom_backup = dest / f"wisdom-{ts}.md"
            shutil.copy2(wisdom_path, wisdom_backup)
            return {
                "component": "wisdom",
                "file": str(wisdom_backup),
                "size": wisdom_backup.stat().st_size,
            }
        return None

    def _backup_secrets(self, dest: Path, ts: str) -> dict | None:
        """Backup encrypted secrets and key file."""
        secrets_path = settings.secrets_file
        if secrets_path.exists():
            secrets_backup = dest / f"secrets-{ts}.enc"
            shutil.copy2(secrets_path, secrets_backup)
            entry = {
                "component": "secrets",
                "file": str(secrets_backup),
                "size": secrets_backup.stat().st_size,
            }
            key_file = settings.secret_key_file
            if key_file.exists():
                key_backup = dest / f"secrets-{ts}.key"
                shutil.copy2(key_file, key_backup)
                entry["key_file"] = str(key_backup)
            return entry
        return None

    def _backup_config(self, dest: Path, ts: str) -> dict | None:
        """Backup config directory as tar.gz."""
        config_dirs = [
            settings.config_dir,
            settings.udos_root / "uCore/config",
        ]
        files_to_backup = []
        for d in config_dirs:
            if d.exists():
                for f in d.rglob("*"):
                    if f.is_file():
                        files_to_backup.append(f)

        if not files_to_backup:
            return None

        backup_file = dest / f"config-{ts}.tar.gz"
        with tarfile.open(backup_file, "w:gz") as tar:
            for f in files_to_backup:
                try:
                    arcname = str(f.relative_to(Path.home()))
                except ValueError:
                    arcname = f.name
                tar.add(f, arcname=arcname)

        return {
            "component": "config",
            "file": str(backup_file),
            "size": backup_file.stat().st_size,
            "files": len(files_to_backup),
        }

    def _cleanup_old_backups(self, dest: Path, retention_days: int) -> int:
        """Remove backups older than retention_days."""
        cutoff = time.time() - (retention_days * 86400)
        removed = 0
        for f in dest.iterdir():
            if f.is_file() and f.stat().st_mtime < cutoff:
                f.unlink()
                removed += 1
            elif f.is_dir() and f.stat().st_mtime < cutoff:
                shutil.rmtree(f)
                removed += 1
        if removed:
            log.info("Cleaned up %d old backups", removed)
        return removed
