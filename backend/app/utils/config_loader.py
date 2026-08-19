"""Shared config loader for uCore YAML configuration files.

Reads YAML files from ``$UDOS_HOME/config`` with safe fallback defaults.
Used by server.py, system_api.py, and developer_api.py to replace
hardcoded policy/service/page arrays.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from app.core.settings import settings

log = logging.getLogger("ucore.config")


def _config_dir() -> Path:
    """Return the config directory path."""
    env_dir = os.environ.get("UCORE_CONFIG_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    return settings.config_dir


def _read_yaml(filename: str) -> dict[str, Any] | None:
    """Read a YAML file from the config directory.  Returns None if missing."""
    path = _config_dir() / filename
    if not path.exists():
        log.debug("Config file not found (using defaults): %s", path)
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if not isinstance(data, dict):
            log.warning("Config file is not a dict: %s", path)
            return None
        return data
    except Exception:
        log.warning("Failed to load config file: %s", path, exc_info=True)
        return None


# ─── Service Registry ────────────────────────────────────────────────────

_DEFAULT_SERVICES: list[dict[str, Any]] = [
    {
        "id": "snackbar",
        "name": "Snackbar",
        "category": "system",
        "host": "localhost",
        "port": 8484,
        "health": {"path": "/api/health"},
        "description": "Container orchestrator and workflow runner",
    },
    {
        "id": "ollama",
        "name": "Ollama",
        "category": "system",
        "host": "localhost",
        "port": 11434,
        "health": {"path": "/api/tags", "accept_status": [200]},
        "description": "Local LLM inference runtime",
    },
    {
        "id": "feed-spool",
        "name": "Feed Spool",
        "category": "system",
        "host": "localhost",
        "port": 8486,
        "health": {"path": "/health"},
        "description": "Feed spooler and transport layer",
    },
    {
        "id": "secret-server",
        "name": "Secret Server",
        "category": "user",
        "host": "localhost",
        "port": 30001,
        "health": {"path": "/health", "enabled": True},
        "tcp_probe": True,
        "description": "AES-256-GCM encrypted secret vault",
    },
]

_DEFAULT_PROBE = {
    "timeout_seconds": 2,
    "accept_status": [200],
}


def load_service_registry() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load service definitions and probe defaults from config.

    Returns (services, probe_config).
    Falls back to _DEFAULT_SERVICES if the config file is missing.
    """
    data = _read_yaml("service-registry.yaml")
    if data is None:
        log.debug("Service registry: using built-in defaults")
        return _DEFAULT_SERVICES, _DEFAULT_PROBE

    services: list[dict[str, Any]] = data.get("services", [])
    probe: dict[str, Any] = data.get("probe", _DEFAULT_PROBE)

    if not services:
        log.warning("Service registry config has empty services; using defaults")
        return _DEFAULT_SERVICES, _DEFAULT_PROBE

    return services, probe


# ─── Developer Repo Policy ───────────────────────────────────────────────

_DEFAULT_SYSTEM_REPO_NAMES: set[str] = {
    "ucore", "uflow", "uknowledge", "ucode", "ucode2", "uvector",
}

_DEFAULT_CORE_REPO_NAMES: set[str] = {
    "ucore-developer",
}

_DEFAULT_EXTENSION_REPO_NAMES: set[str] = {
    "udos-budget", "udos-identity", "udos-google",
    "udos-dreamscape", "udos-publishing", "udos-agents", "udos-vaults",
}

_DEFAULT_VAULT_DOC_NAME_HINTS: set[str] = {
    "global-knowledge",
    "doc-sites",
    "knowledge-base",
    "docs-library",
    "vault",
}

_DEFAULT_CODE_MARKER_FILES: set[str] = {
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "go.mod",
    "cargo.toml",
    "pom.xml",
    "build.gradle",
    "makefile",
}

_DEFAULT_CODE_MARKER_DIRS: set[str] = {
    "src", "backend", "frontend", "frontend-vue", "app", "scripts", "packages",
}

_DEFAULT_DOC_MARKER_DIRS: set[str] = {
    ".obsidian", "docs", "knowledge", "notes",
}

_DEFAULT_CODE_FILE_EXTENSIONS: set[str] = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java",
    ".c", ".cpp", ".h", ".hpp", ".rb", ".php", ".swift", ".kt",
    ".scala", ".cs", ".sh",
}

_DEFAULT_DOC_FILE_EXTENSIONS: set[str] = {
    ".md", ".mdx", ".markdown", ".rst", ".txt",
}

_DEFAULT_DOC_ONLY_THRESHOLD: dict[str, int] = {
    "min_doc_files": 20,
    "max_code_files": 0,
}

_DEFAULT_SCAN_LIMITS: dict[str, int] = {
    "max_git_files_to_scan": 1200,
}

_DEFAULT_BEHAVIOR: dict[str, Any] = {
    "fallback_kind_when_uncertain": "code",
    "include_kind_metadata": True,
}

_DEFAULT_VAULT_NON_CODE_ROOTS: list[str] = [
    "~/Vault",
    "~/Shared",
    "~/Public",
]

_DEFAULT_CODE_ROOT: str = "~/Code"


def load_developer_repo_policy() -> dict[str, Any]:
    """Load developer repo classification policy from config.

    Returns a dict with all policy keys; falls back to built-in defaults.
    """
    data = _read_yaml("developer-repo-policy.yaml")
    if data is None:
        log.debug("Developer repo policy: using built-in defaults")
        return _build_default_policy()

    roots = data.get("roots", {})
    policy = data.get("policy", {})
    classification = data.get("classification", {})
    behavior = data.get("behavior", {})

    return {
        "code_root": roots.get("code_root", _DEFAULT_CODE_ROOT),
        "vault_non_code_roots": roots.get(
            "vault_non_code_roots", _DEFAULT_VAULT_NON_CODE_ROOTS,
        ),
        "system_repos": set(
            data.get("system_repos", list(_DEFAULT_SYSTEM_REPO_NAMES)),
        ),
        "core_repos": set(
            data.get("core_repos", list(_DEFAULT_CORE_REPO_NAMES)),
        ),
        "extension_repos": set(
            data.get("extension_repos", list(_DEFAULT_EXTENSION_REPO_NAMES)),
        ),
        "vault_doc_name_hints": set(
            data.get("vault_doc_name_hints", list(_DEFAULT_VAULT_DOC_NAME_HINTS)),
        ),
        "code_marker_files": set(
            _lower_keys(
                data.get("code_markers", {}).get(
                    "files", list(_DEFAULT_CODE_MARKER_FILES),
                ),
            ),
        ),
        "code_marker_dirs": set(
            _lower_keys(
                data.get("code_markers", {}).get(
                    "dirs", list(_DEFAULT_CODE_MARKER_DIRS),
                ),
            ),
        ),
        "doc_marker_dirs": set(
            _lower_keys(
                classification.get(
                    "doc_marker_dirs",
                    list(_DEFAULT_DOC_MARKER_DIRS),
                ),
            ),
        ),
        "code_file_extensions": set(
            classification.get(
                "code_file_extensions",
                list(_DEFAULT_CODE_FILE_EXTENSIONS),
            ),
        ),
        "doc_file_extensions": set(
            classification.get(
                "doc_file_extensions",
                list(_DEFAULT_DOC_FILE_EXTENSIONS),
            ),
        ),
        "doc_only_threshold": classification.get(
            "doc_only_threshold", _DEFAULT_DOC_ONLY_THRESHOLD,
        ),
        "scan_limits": classification.get(
            "scan_limits", _DEFAULT_SCAN_LIMITS,
        ),
        "default_scope": policy.get("default_scope", "code"),
        "scopes_allowed": policy.get(
            "scopes_allowed",
            ["code", "all", "vault", "system"],
        ),
        "exclude_system_default": policy.get(
            "exclude_system_default", False,
        ),
        "fallback_kind": behavior.get(
            "fallback_kind_when_uncertain",
            _DEFAULT_BEHAVIOR["fallback_kind_when_uncertain"],
        ),
        "include_kind_metadata": behavior.get(
            "include_kind_metadata",
            _DEFAULT_BEHAVIOR["include_kind_metadata"],
        ),
    }


def _build_default_policy() -> dict[str, Any]:
    """Return the full default policy dict."""
    return {
        "code_root": _DEFAULT_CODE_ROOT,
        "vault_non_code_roots": _DEFAULT_VAULT_NON_CODE_ROOTS,
        "system_repos": _DEFAULT_SYSTEM_REPO_NAMES,
        "core_repos": _DEFAULT_CORE_REPO_NAMES,
        "extension_repos": _DEFAULT_EXTENSION_REPO_NAMES,
        "vault_doc_name_hints": _DEFAULT_VAULT_DOC_NAME_HINTS,
        "code_marker_files": _DEFAULT_CODE_MARKER_FILES,
        "code_marker_dirs": _DEFAULT_CODE_MARKER_DIRS,
        "doc_marker_dirs": _DEFAULT_DOC_MARKER_DIRS,
        "code_file_extensions": _DEFAULT_CODE_FILE_EXTENSIONS,
        "doc_file_extensions": _DEFAULT_DOC_FILE_EXTENSIONS,
        "doc_only_threshold": _DEFAULT_DOC_ONLY_THRESHOLD,
        "scan_limits": _DEFAULT_SCAN_LIMITS,
        "default_scope": "code",
        "scopes_allowed": ["code", "all", "vault", "system"],
        "exclude_system_default": False,
        "fallback_kind": "project",
        "include_kind_metadata": True,
    }


def _lower_keys(items: list[str]) -> list[str]:
    """Lowercase a list of strings for case-insensitive comparison."""
    return [s.lower() for s in items]


# ─── System Pages Registry ───────────────────────────────────────────────

_DEFAULT_S_PAGES: list[dict[str, str]] = [
    {"id": "S100", "title": "Page Not Found", "icon": "search_off"},
    {"id": "S101", "title": "Server Offline", "icon": "cloud_off"},
    {"id": "S300", "title": "Internal Server Error", "icon": "error"},
    {"id": "S310", "title": "Request Timed Out", "icon": "timer_off"},
    {"id": "S320", "title": "Access Restricted", "icon": "lock"},
    {"id": "S330", "title": "Configuration Missing", "icon": "settings"},
    {"id": "S340", "title": "Dependency Unavailable", "icon": "link_off"},
    {"id": "S600", "title": "Help and Recovery", "icon": "help"},
]

_REQUIRED_PAGE_FIELDS = {"id", "title", "icon"}


def load_system_pages_registry() -> list[dict]:
    """Load S-pages from config.

    Returns a list of S-pages and falls back to built-in defaults.
    Validates that every page has id, title, and icon fields.
    """
    data = _read_yaml("system-pages-registry.yaml")
    if data is None:
        log.debug(
            "System pages registry: using built-in defaults",
        )
        return _DEFAULT_S_PAGES

    pages = data.get("pages", {})
    if not isinstance(pages, dict):
        log.warning(
            "System pages registry: invalid 'pages' key; using defaults",
        )
        return _DEFAULT_S_PAGES

    s_pages_raw: list[dict] = pages.get("s", [])

    s_pages = _validate_pages(s_pages_raw, "S")

    if not s_pages:
        s_pages = _DEFAULT_S_PAGES

    return s_pages


def _validate_pages(raw: list[dict], prefix: str) -> list[dict]:
    """Filter pages to only those with required fields."""
    valid: list[dict] = []
    for entry in raw:
        if not isinstance(entry, dict):
            continue
        missing = _REQUIRED_PAGE_FIELDS - set(entry.keys())
        if missing:
            log.warning(
                "Skipping %s-page entry missing fields: %s",
                prefix,
                missing,
            )
            continue
        valid.append(entry)
    return valid
