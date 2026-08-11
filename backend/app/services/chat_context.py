"""Chat Context Enrichment for uCore chat prompts.

Gathers vault documents, repo snippets, and skill metadata to enrich
system prompts before routing to the LLM.
"""
from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any

log = logging.getLogger("ucore.chat_context")

VAULT_ROOTS = [
    Path.home() / "Vault",
    Path.home() / "Shared",
    Path.home() / "Public",
]

REPO_ROOTS = [
    Path.home() / "Code" / "uCore",
    Path.home() / "Code" / "uCode",
]

MAX_CONTEXT_CHARS = 4000
MAX_VAULT_FILES = 5
MAX_REPO_SNIPPETS = 5

def _scan_vault_for_query(query: str) -> list[dict[str, Any]]:
    """Scan vault directories for markdown files matching the query."""
    results: list[dict[str, Any]] = []
    keywords = query.lower().split()
    for vault_root in VAULT_ROOTS:
        if not vault_root.exists() or len(results) >= MAX_VAULT_FILES:
            continue
        vault_name = vault_root.name
        try:
            for md_file in vault_root.rglob("*.md"):
                if len(results) >= MAX_VAULT_FILES:
                    break
                try:
                    text = md_file.read_text(encoding="utf-8", errors="ignore")
                    text_lower = text.lower()
                    matches = sum(1 for kw in keywords if kw in text_lower)
                    if matches > 0:
                        frontmatter: dict[str, str] = {}
                        content_preview = text
                        if text.startswith("---"):
                            parts = text.split("---", 2)
                            if len(parts) >= 3:
                                for fl in parts[1].strip().split("\n"):
                                    if ": " in fl:
                                        k, _, v = fl.partition(": ")
                                        frontmatter[k.strip()] = v.strip()
                                content_preview = parts[2].strip()
                        preview = content_preview[:500]
                        if len(content_preview) > 500:
                            preview += "..."
                        rel_path = str(md_file.relative_to(vault_root))
                        results.append({
                            "path": f"~/{vault_name}/{rel_path}",
                            "vault": vault_name,
                            "frontmatter": frontmatter,
                            "preview": preview,
                            "score": matches,
                        })
                except Exception:
                    continue
        except Exception as e:
            log.debug("Error scanning vault %s: %s", vault_root, e)
    return sorted(results, key=lambda r: r["score"], reverse=True)


def _scan_repos_for_query(query: str) -> list[dict[str, Any]]:
    """Use git grep to find relevant code snippets in monitored repos."""
    results: list[dict[str, Any]] = []
    keywords = query.lower().split()
    if not keywords:
        return results
    for repo_root in REPO_ROOTS:
        if not repo_root.exists() or not (repo_root / ".git").exists():
            continue
        if len(results) >= MAX_REPO_SNIPPETS:
            break
        try:
            pattern = "\\|".join(kw for kw in keywords[:3])
            proc = subprocess.run(
                ["git", "grep", "-n", "-i", pattern, "--",
                 "*.py", "*.ts", "*.vue", "*.yaml", "*.json", "*.md"],
                cwd=str(repo_root), capture_output=True, text=True, timeout=10,
            )
            if proc.returncode != 0:
                continue
            for line in proc.stdout.strip().split("\n")[:MAX_REPO_SNIPPETS * 3]:
                if ":" not in line:
                    continue
                file_part, _, rest = line.partition(":")
                if ":" not in rest:
                    continue
                lineno, _, snippet = rest.partition(":")
                results.append({
                    "repo": repo_root.name,
                    "file": file_part,
                    "line": lineno,
                    "snippet": snippet.strip()[:200],
                })
            if len(results) >= MAX_REPO_SNIPPETS:
                break
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            log.debug("Repo scan failed for %s: %s", repo_root, e)
def _list_available_skills() -> list[dict[str, Any]]:
    """List available uCore skills from the skills directory."""
    skills: list[dict[str, Any]] = []
    skills_dir = Path(__file__).resolve().parent.parent / "skills" / "builtin"
    if not skills_dir.exists():
        return skills
    try:
        for skill_file in sorted(skills_dir.glob("skill_*.py")):
            name = skill_file.stem.replace("skill_", "")
            label = name.replace("_", " ").title()
            skills.append({"id": name, "label": label, "file": skill_file.name})
    except Exception as e:
        log.debug("Error listing skills: %s", e)
    return skills[:10]


def gather_chat_context(query: str, mode: str = "plan") -> dict[str, Any]:
    """Gather context from vaults, repos, and skills for chat enrichment.

    Args:
        query: The user search query or message.
        mode: The chat mode (plan, act, chat).

    Returns:
        Dict with vault_docs, repo_snippets, skills, and context_string.
    """
    result: dict[str, Any] = {
        "vault_docs": [],
        "repo_snippets": [],
        "skills": [],
        "context_string": "",
    }
    if mode not in ("plan", "act"):
        return result

    result["vault_docs"] = _scan_vault_for_query(query)
    result["repo_snippets"] = _scan_repos_for_query(query)
    result["skills"] = _list_available_skills()

    parts: list[str] = []
    if result["vault_docs"]:
        parts.append("## Vault Documents\n")
        for doc in result["vault_docs"]:
            parts.append(f"- {doc['path']}")
            if doc.get("frontmatter"):
                fm_str = ", ".join(
                    f"{k}={v}" for k, v in doc["frontmatter"].items()
                )
                parts.append(f"  (metadata: {fm_str})")
            parts.append(f"  Preview: {doc['preview'][:200]}")
            parts.append("")

    if result["repo_snippets"]:
        parts.append("## Code Repository Snippets\n")
        for snip in result["repo_snippets"]:
            parts.append(
                f"- [{snip['repo']}] {snip['file']}:{snip['line']}"
            )
            parts.append(f"  {snip['snippet']}")
            parts.append("")

    if result["skills"]:
        parts.append("## Available Skills\n")
        for skill in result["skills"]:
            parts.append(f"- {skill['id']}: {skill['label']}")

    context_str = "\n".join(parts)
    if len(context_str) > MAX_CONTEXT_CHARS:
        context_str = context_str[:MAX_CONTEXT_CHARS] + "\n... (context truncated)"
    result["context_string"] = context_str

    log.info(
        "Context gathered: %d vault docs, %d repo snippets, %d skills (%d chars)",
        len(result["vault_docs"]), len(result["repo_snippets"]),
        len(result["skills"]), len(context_str),
    )
    return result

    return results[:MAX_REPO_SNIPPETS]
