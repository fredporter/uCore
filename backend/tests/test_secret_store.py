"""Unit tests for the SecretStore (AES-256-GCM encrypted)."""

from __future__ import annotations

from app.secret.store import SecretStore


class TestSecretStore:
    """Test SecretStore in in-memory mode (no file I/O)."""

    def setup_method(self):
        self.store = SecretStore()
        self.store._secrets = {}
        self.store._dirty = False

    def test_set_and_get(self):
        self.store.set("API_KEY", "sk-test-12345")
        assert self.store.get("API_KEY") == "sk-test-12345"

    def test_get_nonexistent(self):
        assert self.store.get("DOES_NOT_EXIST") is None

    def test_get_default(self):
        assert self.store.get("MISSING", "default_val") == "default_val"

    def test_delete_existing(self):
        self.store.set("DELETE_ME", "value")
        assert self.store.delete("DELETE_ME") is True
        assert self.store.get("DELETE_ME") is None

    def test_delete_nonexistent(self):
        assert self.store.delete("ALREADY_GONE") is False

    def test_list_empty(self):
        assert self.store.list() == []

    def test_list_masked(self):
        self.store.set("LONG_KEY", "abcdefghijklmnop")
        self.store.set("SHORT", "ab")
        secrets = self.store.list()
        assert len(secrets) == 2
        names = {s["name"] for s in secrets}
        assert "LONG_KEY" in names
        assert "SHORT" in names
        long_secret = next(s for s in secrets if s["name"] == "LONG_KEY")
        assert "****" in long_secret["masked"]
        assert long_secret["masked"].startswith("abcd")

    def test_set_dirty_flag(self):
        assert self.store._dirty is False
        self.store.set("KEY", "val")
        assert self.store._dirty is True

    def test_delete_dirty_flag(self):
        self.store.set("KEY", "val")
        self.store._dirty = False
        self.store.delete("KEY")
        assert self.store._dirty is True

    def test_multiple_keys(self):
        self.store.set("A", "1")
        self.store.set("B", "2")
        self.store.set("C", "3")
        assert len(self.store.list()) == 3
        assert self.store.get("A") == "1"
        assert self.store.get("B") == "2"
        assert self.store.get("C") == "3"

    def test_overwrite_key(self):
        self.store.set("KEY", "old_value")
        self.store.set("KEY", "new_value")
        assert self.store.get("KEY") == "new_value"
        assert len(self.store.list()) == 1


def test_sync_from_env(monkeypatch):
    """Test that sync_from_env imports known env vars."""
    from app.secret.store import SecretStore

    store = SecretStore()
    store._secrets = {}
    store._dirty = False

    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.setenv("GITHUB_TOKEN", "gh_test_token")
    monkeypatch.setenv("RANDOM_VAR", "should_not_import")

    store.sync_from_env()

    assert store.get("OPENROUTER_API_KEY") == "sk-or-test"
    assert store.get("GITHUB_TOKEN") == "gh_test_token"
    assert store.get("RANDOM_VAR") is None


def test_get_all_env_vars(monkeypatch):
    """get_all_env_vars returns store values + env overrides."""
    from app.secret.store import SecretStore

    store = SecretStore()
    store._secrets = {}
    store.set("STORE_KEY", "store_value")
    monkeypatch.setenv("STORE_KEY", "env_override")
    monkeypatch.setenv("EXTRA_ENV", "extra")

    all_vars = store.get_all_env_vars()
    assert all_vars["STORE_KEY"] == "env_override"
    assert "EXTRA_ENV" not in all_vars


def test_encrypted_roundtrip_and_tamper_fails_closed(tmp_path, monkeypatch):
    import pytest

    import app.secret.store as module

    monkeypatch.setattr(module, "SECRETS_DIR", tmp_path)
    monkeypatch.setattr(module, "SECRETS_FILE", tmp_path / "secrets.enc")
    monkeypatch.setattr(module, "KEY_FILE", tmp_path / "key")
    monkeypatch.setattr(module, "DATA_DIR", tmp_path / "data")
    original = module.SecretStore()
    original.set("EXAMPLE", "private-value")
    original.save()
    assert b"private-value" not in module.SECRETS_FILE.read_bytes()
    assert module.SECRETS_FILE.stat().st_mode & 0o777 == 0o600
    loaded = module.SecretStore()
    loaded.load()
    assert loaded.get("EXAMPLE") == "private-value"
    before = module.SECRETS_FILE.read_bytes()
    module.SECRETS_FILE.write_bytes(before[:-1] + bytes([before[-1] ^ 1]))
    with pytest.raises(RuntimeError, match="Cannot decrypt"):
        loaded.load()
    module.KEY_FILE.unlink()
    with pytest.raises(RuntimeError, match="key is missing"):
        module.SecretStore().load()


def test_encryption_unavailable_never_writes_plaintext(tmp_path, monkeypatch):
    import pytest

    import app.secret.store as module

    monkeypatch.setattr(module, "AESGCM", None)
    monkeypatch.setattr(module, "DATA_DIR", tmp_path)
    store = module.SecretStore()
    store.set("EXAMPLE", "private-value")
    with pytest.raises(RuntimeError, match="cryptography"):
        store.save()
    assert not (tmp_path / "secrets.json").exists()


def test_legacy_migration_verifies_before_removing_plaintext(tmp_path, monkeypatch):
    import json

    import app.secret.store as module

    monkeypatch.setattr(module, "SECRETS_DIR", tmp_path)
    monkeypatch.setattr(module, "SECRETS_FILE", tmp_path / "secrets.enc")
    monkeypatch.setattr(module, "KEY_FILE", tmp_path / "key")
    monkeypatch.setattr(module, "DATA_DIR", tmp_path)
    legacy = tmp_path / "secrets.json"
    legacy.write_text(json.dumps({"EXAMPLE": "private-value"}))
    store = module.SecretStore()
    store.load()
    assert store.get("EXAMPLE") == "private-value"
    assert module.SECRETS_FILE.exists() and not legacy.exists()
