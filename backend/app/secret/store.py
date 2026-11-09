"""AES-256-GCM encrypted secret store for uCore.

Stores API keys and credentials encrypted beneath ``$UDOS_HOME/secrets``.
Uses a product-owned 256-bit key with owner-only file permissions.
"""

from __future__ import annotations

import json
import logging
import os
import secrets as pysecrets
from datetime import UTC, datetime
from typing import Any

from app.core.settings import settings

AESGCM: Any
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM as _AESGCM

    AESGCM = _AESGCM
except ImportError:
    AESGCM = None

log = logging.getLogger("ucore.secret")

SECRETS_DIR = settings.secrets_dir
SECRETS_FILE = settings.secrets_file
KEY_FILE = settings.secret_key_file
DATA_DIR = settings.data_dir
AUDIT_FILE = settings.secrets_dir / "secrets.audit.jsonl"


def _derive_key(master_key: bytes) -> bytes:
    """Derive a 256-bit AES key using HKDF."""
    if len(master_key) == 32:
        return master_key
    from cryptography.hazmat.primitives import hashes  # type: ignore
    from cryptography.hazmat.primitives.hkdf import HKDF  # type: ignore

    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"ucore-secret-store-v1",
    )
    return hkdf.derive(master_key)


def _generate_key() -> bytes:
    """Generate a new 256-bit master key."""
    return pysecrets.token_bytes(32)


def _get_or_create_key() -> bytes:
    """Get existing key or create a new one."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    if KEY_FILE.exists():
        return KEY_FILE.read_bytes()
    if SECRETS_FILE.exists():
        raise RuntimeError("Secret encryption key is missing; restore it before starting")
    key = _generate_key()
    try:
        fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return KEY_FILE.read_bytes()
    with os.fdopen(fd, "wb") as stream:
        stream.write(key)
    return key


class SecretStore:
    """Encrypted key-value store for secrets."""

    def __init__(self):
        self._key = None
        self._secrets: dict[str, str] = {}
        self._dirty = False
        self._audit_file = AUDIT_FILE

    def _record_audit(
        self,
        action: str,
        key: str,
        actor: str = "system",
        metadata: dict | None = None,
    ) -> None:
        """Append a minimal audit event without persisting secret values."""
        try:
            self._audit_file.parent.mkdir(parents=True, exist_ok=True)
            event = {
                "timestamp": datetime.now(UTC).isoformat(),
                "action": action,
                "key": key,
                "actor": actor,
                "metadata": metadata or {},
            }
            with self._audit_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=True) + "\n")
        except Exception as e:
            log.debug("Failed to write secret audit event: %s", e)

    def list_audit(self, limit: int = 100) -> list[dict]:
        """Return most recent audit events (newest first)."""
        if not self._audit_file.exists():
            return []

        try:
            lines = self._audit_file.read_text(encoding="utf-8").splitlines()
        except Exception:
            return []

        events: list[dict] = []
        for line in reversed(lines[-max(limit * 2, 200) :]):
            if len(events) >= limit:
                break
            try:
                parsed = json.loads(line)
                if isinstance(parsed, dict):
                    events.append(parsed)
            except Exception:
                continue
        return events

    def load(self):
        """Load and decrypt secrets from disk."""
        if AESGCM is None:
            raise RuntimeError(
                "Encrypted secret storage requires cryptography; plaintext fallback is disabled"
            )
        self._key = _get_or_create_key()
        if not SECRETS_FILE.exists():
            self._secrets = {}
            self._migrate_legacy()
            return
        try:
            data = SECRETS_FILE.read_bytes()
            decrypted = AESGCM(_derive_key(self._key)).decrypt(data[:12], data[12:], None)
            payload = json.loads(decrypted)
            if not isinstance(payload, dict):
                raise ValueError("Invalid secret payload")
        except Exception:
            raise RuntimeError(
                "Cannot decrypt secret store; restore the matching key/store before saving"
            ) from None
        self._secrets = payload
        KEY_FILE.chmod(0o600)
        SECRETS_FILE.chmod(0o600)
        self._migrate_legacy()

    def _migrate_legacy(self):
        legacy = DATA_DIR / "secrets.json"
        if not legacy.exists():
            return
        payload = json.loads(legacy.read_text())
        if not isinstance(payload, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in payload.items()
        ):
            raise RuntimeError("Legacy secret store is invalid; no files changed")
        conflicts = {
            k: v for k, v in payload.items() if k in self._secrets and self._secrets[k] != v
        }
        if conflicts:
            # Keep competing legacy values encrypted without replacing live credentials.
            backup = "LEGACY_PLAINTEXT_BACKUP_" + pysecrets.token_hex(8)
            self._secrets[backup] = json.dumps(conflicts)
        for key, value in payload.items():
            self._secrets.setdefault(key, value)
        self._dirty = True
        self.save()
        data = SECRETS_FILE.read_bytes()
        verified = json.loads(AESGCM(_derive_key(self._key)).decrypt(data[:12], data[12:], None))
        if verified != self._secrets:
            raise RuntimeError("Secret migration verification failed")
        legacy.unlink()
        log.info(
            "Migrated legacy secrets to encrypted storage; competing values retained in encrypted backup"
        )

    def save(self):
        """Write encrypted data atomically; never fall back to plaintext."""
        if AESGCM is None:
            raise RuntimeError("Encrypted secret storage requires cryptography")
        if not self._dirty:
            return
        import tempfile

        self._key = _get_or_create_key()
        nonce = pysecrets.token_bytes(12)
        ciphertext = AESGCM(_derive_key(self._key)).encrypt(
            nonce, json.dumps(self._secrets).encode(), None
        )
        SECRETS_DIR.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(
                dir=SECRETS_DIR, prefix="secrets-", delete=False
            ) as stream:
                temporary = stream.name
                stream.write(nonce + ciphertext)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, SECRETS_FILE)
        finally:
            if temporary and os.path.exists(temporary):
                os.unlink(temporary)
        self._dirty = False

    def get(
        self,
        key: str,
        default: str | None = None,
        actor: str = "system",
    ) -> str | None:
        """Get a secret by key."""
        value = self._secrets.get(key, default)
        if actor != "system":
            self._record_audit(
                "read",
                key,
                actor,
                {"found": value is not None},
            )
        return value

    def set(self, key: str, value: str, actor: str = "system"):
        """Set a secret (marked dirty, saved on next save)."""
        self._secrets[key] = value
        self._dirty = True
        if actor != "system":
            self._record_audit("write", key, actor)

    def delete(self, key: str, actor: str = "system") -> bool:
        """Delete a secret."""
        if key in self._secrets:
            del self._secrets[key]
            self._dirty = True
            if actor != "system":
                self._record_audit("delete", key, actor)
            return True
        if actor != "system":
            self._record_audit("delete-miss", key, actor)
        return False

    def list(self) -> list[dict]:
        """List all secret keys (values masked)."""
        return [
            {"name": k, "masked": v[:4] + "****" if len(v) > 8 else "****"}
            for k, v in sorted(self._secrets.items())
        ]

    def get_all_env_vars(self) -> dict[str, str]:
        """Get all secrets + matching env vars."""
        result = {}
        # From store
        for k, v in self._secrets.items():
            result[k] = v
        # From env (override)
        for k in list(result.keys()):
            env_val = os.environ.get(k)
            if env_val:
                result[k] = env_val
        return result

    def sync_from_env(self):
        """Import known env vars into the store."""
        known_keys = [
            "OPENROUTER_API_KEY",
            "GITHUB_TOKEN",
            "ANTHROPIC_API_KEY",
            "MISTRAL_API_KEY",
            "DEEPSEEK_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "GROQ_API_KEY",
            "HUGGINGFACE_TOKEN",
            "REPLICATE_API_KEY",
            "COHERE_API_KEY",
            "AI21_API_KEY",
        ]
        changed = False
        for key in known_keys:
            val = os.environ.get(key)
            if val and key not in self._secrets:
                self._secrets[key] = val
                self._record_audit("import-env", key, "startup")
                changed = True
                log.info(f"Imported {key} from environment")
        if changed:
            self._dirty = True
            self.save()


# Singleton
_store: SecretStore | None = None


def get_store() -> SecretStore:
    global _store
    if _store is None:
        _store = SecretStore()
        _store.load()
        _store.sync_from_env()
    return _store
