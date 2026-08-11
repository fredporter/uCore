#!/usr/bin/env python3
"""
uDev Automation Engine
=======================
Orchestrates the global-knowledge pipeline:
  Scan → Parse → Scrape → Citations → Index → Notebook → Commit

Usage:
    python engine.py              # Full pipeline
    python engine.py --dry-run    # Preview without writing
    python engine.py --topic binder  # Process a single topic
"""

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import yaml


# ═══════════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════════

def load_config(path: Path = None) -> dict:
    """Load config.yaml, expand paths, and return a settings dict."""
    if path is None:
        path = Path(__file__).resolve().parent / "config.yaml"
    with open(path) as f:
        cfg = yaml.safe_load(f)
    for key in ("knowledge_root", "repo_root"):
        if key in cfg:
            cfg[key] = str(Path(cfg[key]).expanduser().resolve())
    return cfg


# ═══════════════════════════════════════════════════════════════════
# Step 1: Scan — find new or modified markdown files
# ═══════════════════════════════════════════════════════════════════

def scan_knowledge_tree(root: Path, exclude_dirs: list[str]) -> list[dict]:
    """Walk the global-knowledge tree and return file metadata dicts."""
    entries = []
    exclude = set(exclude_dirs)
    for md_file in sorted(root.rglob("*.md")):
        if any(p.name in exclude for p in md_file.parents):
            continue
        if md_file.name == "SUMMARY.md":
            continue
        stat = md_file.stat()
        entries.append({
            "path": str(md_file.relative_to(root)),
            "abs_path": str(md_file),
            "mtime": stat.st_mtime,
            "size": stat.st_size,
        })
    return entries

# ═══════════════════════════════════════════════════════════════════
# Step 2: Parse — extract front‑matter
# ═══════════════════════════════════════════════════════════════════

def parse_frontmatter(filepath: str) -> dict:
    """Extract YAML front‑matter from a markdown file."""
    try:
        import frontmatter
        post = frontmatter.load(filepath)
        return {
            "title": post.get("title", Path(filepath).stem),
            "domain": post.get("domain", ""),
            "status": post.get("status", "draft"),
            "date": str(post.get("date", post.get("created", ""))),
            "author": post.get("author", "uDev"),
            "tags": post.get("tags", []),
            "body": post.content,
            "metadata": dict(post.metadata),
        }
    except ImportError:
        with open(filepath) as f:
            content = f.read()
        meta = {}
        body = content
        fm_match = re.match(r'^---\s*\n(.*?)\n---\s*\n', content, re.DOTALL)
        if fm_match:
            try:
                meta = yaml.safe_load(fm_match.group(1)) or {}
            except yaml.YAMLError:
                pass
            body = content[fm_match.end():]
        h1_match = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
        title = h1_match.group(1) if h1_match else Path(filepath).stem
        return {
            "title": meta.get("title", title),
            "domain": meta.get("domain", ""),
            "status": meta.get("status", "draft"),
            "date": str(meta.get("date", meta.get("created", ""))),
            "author": meta.get("author", "uDev"),
            "tags": meta.get("tags", []),
            "body": body,
            "metadata": meta,
        }

# ═══════════════════════════════════════════════════════════════════
# Step 3: Scrape — fetch references via BrowserUI
# ═══════════════════════════════════════════════════════════════════

def scrape_references(endpoint: str, topic: str, body: str,
                      max_refs: int = 5, timeout: int = 30,
                      max_retries: int = 3, backoff: float = 2.0) -> list[dict]:
    """Call BrowserUI endpoint to find supporting web references."""
    import requests
    headings = re.findall(r'^#{1,3}\s+(.+)$', body, re.MULTILINE)
    queries = [topic] + headings[:3]
    references = []
    seen_urls = set()
    for query in queries[:3]:
        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    f"{endpoint}/scrape",
                    json={"query": query, "max_results": 3},
                    timeout=timeout,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("results", []):
                        url = item.get("url", "")
                        if url and url not in seen_urls:
                            seen_urls.add(url)
                            references.append({
                                "title": item.get("title", url),
                                "url": url,
                                "snippet": item.get("snippet", ""),
                            })
                    break
                elif resp.status_code == 429:
                    time.sleep(backoff ** attempt)
                else:
                    break
            except requests.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(backoff ** attempt)
        if len(references) >= max_refs:
            break
    return references[:max_refs]

# ═══════════════════════════════════════════════════════════════════
# Step 4: Citations — insert footnotes into markdown
# ═══════════════════════════════════════════════════════════════════

def generate_citations(filepath: str, body: str, references: list[dict]) -> str:
    """Insert a ## References section with numbered footnotes."""
    if not references:
        return body
    citation_lines = []
    for i, ref in enumerate(references, 1):
        title = ref.get("title", "Untitled")
        url = ref.get("url", "")
        snippet = ref.get("snippet", "")
        citation_lines.append(f"[^{i}]: [{title}]({url}) — {snippet}")
    citation_block = "\n".join(citation_lines)
    ref_match = re.search(r'^## References\s*\n', body, re.MULTILINE)
    if ref_match:
        insert_pos = ref_match.end()
        next_section = re.search(r'^## ', body[insert_pos:], re.MULTILINE)
        if next_section:
            insert_pos += next_section.start()
        else:
            insert_pos = len(body)
        updated = body[:insert_pos].rstrip() + "\n\n" + citation_block + "\n\n" + body[insert_pos:].lstrip()
    else:
        updated = body.rstrip() + "\n\n## References\n\n" + citation_block + "\n"
    return updated


# ═══════════════════════════════════════════════════════════════════
# Step 5: Index — update SUMMARY.md
# ═══════════════════════════════════════════════════════════════════

def update_summary_index(knowledge_root: Path, entries: list[dict]) -> str:
    """Generate a SUMMARY.md table of contents from scanned entries."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Global Knowledge Index", "",
        f"*Auto-generated by automation/engine.py — {now}*", "",
        "## Topics", "",
    ]
    domains: dict[str, list[dict]] = {}
    for entry in entries:
        parts = Path(entry["path"]).parts
        domain = parts[0] if len(parts) > 1 else "root"
        domains.setdefault(domain, []).append(entry)
    for domain in sorted(domains):
        lines.append(f"### {domain}")
        lines.append("")
        for entry in domains[domain]:
            display = Path(entry["path"]).stem.replace("-", " ").title()
            lines.append(f"- [{display}]({entry['path']})")
        lines.append("")
    lines.extend([
        "---", "",
        f"**{len(entries)} articles across {len(domains)} domains**",
    ])
    return "\n".join(lines) + "\n"
# ═══════════════════════════════════════════════════════════════════
# Step 6: Notebook — convert markdown to .ipynb
# ═══════════════════════════════════════════════════════════════════

def markdown_to_notebook(md_path: str, output_dir: str, kernel: str = "python3") -> str:
    """Convert a markdown file to a Jupyter notebook using nbconvert."""
    md_file = Path(md_path)
    nb_name = md_file.stem + "-demo.ipynb"
    nb_path = Path(output_dir) / nb_name
    try:
        import nbformat
    except ImportError:
        with open(md_path) as f:
            content = f.read()
        nb_json = {
            "cells": [{"cell_type": "markdown", "metadata": {}, "source": content.split("\n")}],
            "metadata": {}, "nbformat": 4, "nbformat_minor": 5,
        }
        with open(nb_path, "w") as f:
            json.dump(nb_json, f, indent=1)
        return str(nb_path)

    with open(md_path) as f:
        content = f.read()
    cells = []
    sections = re.split(r'\n(?=## )', content)
    for section in sections:
        has_code = "```" in section
        if has_code:
            parts = re.split(r'(```.*?\n.*?```)', section, flags=re.DOTALL)
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                if part.startswith("```"):
                    inner = re.sub(r'^```\w*\n', '', part)
                    inner = re.sub(r'\n```$', '', inner)
                    cells.append(nbformat.v4.new_code_cell(inner))
                else:
                    cells.append(nbformat.v4.new_markdown_cell(part))
        else:
            cells.append(nbformat.v4.new_markdown_cell(section.strip()))
    nb = nbformat.v4.new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": f"Python 3 ({kernel})", "language": "python", "name": kernel},
            "language_info": {"name": "python", "version": "3"},
        },
    )
    nbformat.write(nb, str(nb_path))
    return str(nb_path)


# ═══════════════════════════════════════════════════════════════════
# Step 7: Deduplication — hash-based caching
# ═══════════════════════════════════════════════════════════════════

def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}

def save_cache(cache_path: Path, cache: dict) -> None:
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)

def file_changed(abs_path: str, cache: dict, algo: str = "sha256") -> bool:
    h = hashlib.new(algo)
    with open(abs_path, "rb") as f:
        h.update(f.read())
    digest = h.hexdigest()
    prev = cache.get(abs_path)
    if prev != digest:
        cache[abs_path] = digest
        return True
    return False

# ═══════════════════════════════════════════════════════════════════
# Step 8: Git — commit and push to automation branch
# ═══════════════════════════════════════════════════════════════════

def git_commit_and_push(repo_root: str, branch: str, base_branch: str,
                        author_name: str, author_email: str,
                        message: str = "Automated knowledge update") -> bool:
    """Stage changes, commit on automation branch, and push."""
    try:
        import git
    except ImportError:
        print("[WARN] GitPython not installed — skipping git operations.")
        return False
    try:
        repo = git.Repo(repo_root)
    except git.InvalidGitRepositoryError:
        print(f"[ERROR] {repo_root} is not a git repository.")
        return False
    if not repo.is_dirty(untracked_files=True):
        print("[INFO] Working tree clean — nothing to commit.")
        return True
    try:
        current = repo.active_branch.name
        if current != branch:
            if branch in [b.name for b in repo.branches]:
                repo.git.checkout(branch)
            else:
                repo.git.checkout("-b", branch)
    except Exception:
        repo.git.checkout("-b", branch)
    repo.git.add(A=True)
    repo.index.commit(message, author=git.Actor(author_name, author_email))
    try:
        origin = repo.remote("origin")
        origin.push(refspec=f"{branch}:{branch}", set_upstream=True)
        print(f"[OK] Pushed to origin/{branch}")
    except Exception as e:
        print(f"[WARN] Push failed: {e}")
        return False
    return True

    h = hashlib.new(algo)
# ═══════════════════════════════════════════════════════════════════
# Main Pipeline
# ═══════════════════════════════════════════════════════════════════

def run_pipeline(config: dict, dry_run: bool = False, topic_filter: str = None) -> dict:
    """Execute the full pipeline: Scan → Parse → Scrape → Citations → Index → Notebook → Commit."""
    cfg = config
    knowledge_root = Path(cfg["knowledge_root"])
    repo_root = Path(cfg["repo_root"])
    browserui = cfg["browserui_endpoint"]
    scraping_cfg = cfg.get("scraping", {})
    notebook_cfg = cfg.get("notebook", {})
    dedup_cfg = cfg.get("dedup", {})
    git_cfg = cfg.get("git", {})
    scan_cfg = cfg.get("scanning", {})

    cache_path = repo_root / dedup_cfg.get("cache_file", ".automation-cache.json")
    cache = load_cache(cache_path)
    algo = dedup_cfg.get("hash_algorithm", "sha256")

    summary = {"scanned": 0, "changed": 0, "scraped": 0, "cited": 0, "notebooks": 0, "committed": False}

    # Step 1: Scan
    print("=" * 60)
    print("STEP 1: Scanning global-knowledge tree...")
    entries = scan_knowledge_tree(knowledge_root, scan_cfg.get("exclude_dirs", []))
    if topic_filter:
        entries = [e for e in entries if topic_filter in e["path"]]
    summary["scanned"] = len(entries)
    print(f"  Found {len(entries)} markdown files.")
    if not entries:
        return summary

    # Step 2: Parse
    print("\nSTEP 2: Parsing front-matter...")
    changed_files = []
    for entry in entries:
        abs_path = entry["abs_path"]
        changed = file_changed(abs_path, cache, algo)
        if changed or dry_run:
            meta = parse_frontmatter(abs_path)
            entry["meta"] = meta
            changed_files.append(entry)
            status = "NEW/MODIFIED" if changed else "UNCHANGED (dry-run)"
            print(f"  [{status}] {entry['path']} — {meta.get('title', '?')}")

    summary["changed"] = len(changed_files)
    if not changed_files:
        print("  No new or modified files since last run.")
        save_cache(cache_path, cache)
        return summary

    # Process each changed file
    for entry in changed_files:
        meta = entry["meta"]
        topic = meta.get("domain") or Path(entry["path"]).parts[0]
        abs_path = entry["abs_path"]
        body = meta["body"]

        # Step 3: Scrape
        print(f"\n  [{entry['path']}] Scraping references for '{meta['title']}'...")
        references = scrape_references(
            endpoint=browserui, topic=topic, body=body,
            max_refs=scraping_cfg.get("max_references_per_article", 5),
            timeout=scraping_cfg.get("timeout_seconds", 30),
            max_retries=scraping_cfg.get("max_retries", 3),
            backoff=scraping_cfg.get("backoff_factor", 2.0),
        )
        summary["scraped"] += len(references)
        print(f"    Found {len(references)} references.")

        # Step 4: Citations
        if references:
            print("    Inserting citations...")
            updated_body = generate_citations(abs_path, body, references)
            if not dry_run:
                with open(abs_path, "w") as f:
                    if "metadata" in meta and meta["metadata"]:
                        fm = yaml.dump(meta["metadata"], default_flow_style=False, sort_keys=False)
                        f.write(f"---\n{fm}---\n\n{updated_body}")
                    else:
                        f.write(updated_body)
            summary["cited"] += 1

        # Step 6: Notebook
        print("    Generating Jupyter notebook...")
        nb_dir = str(Path(abs_path).parent)
        nb_path = markdown_to_notebook(abs_path, nb_dir, kernel=notebook_cfg.get("kernel", "python3"))
        if not dry_run and nb_path:
            summary["notebooks"] += 1
            print(f"    Notebook: {nb_path}")

    # Step 5: SUMMARY.md
    print("\nSTEP 5: Updating SUMMARY.md...")
    all_entries = scan_knowledge_tree(knowledge_root, scan_cfg.get("exclude_dirs", []))
    summary_md = update_summary_index(knowledge_root, all_entries)
    summary_path = knowledge_root / "SUMMARY.md"
    if not dry_run:
        summary_path.write_text(summary_md)
    print(f"  SUMMARY.md written ({len(summary_md.splitlines())} lines).")

    # Step 7: Save cache
    print("\nSTEP 7: Saving dedup cache...")
    save_cache(cache_path, cache)
    print(f"  Cache saved to {cache_path}")

    # Step 8: Git
    print("\nSTEP 8: Committing and pushing...")
    if not dry_run:
        ok = git_commit_and_push(
            repo_root=str(repo_root),
            branch=git_cfg.get("branch", "automation/updates"),
            base_branch=git_cfg.get("base_branch", "main"),
            author_name=git_cfg.get("author_name", "uDev Automation"),
            author_email=git_cfg.get("author_email", "automation@udev.local"),
        )
        summary["committed"] = ok
        print(f"  {'Committed & pushed' if ok else 'Commit skipped/failed'}")
    else:
        print("  [DRY-RUN] Skipped.")

    return summary


# ═══════════════════════════════════════════════════════════════════
# CLI Entry Point
# ═══════════════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="uDev Automation Engine — ingest, enrich, index, and publish knowledge."
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing or pushing.")
    parser.add_argument("--topic", type=str, default=None, help="Process only matching topic.")
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml.")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else None
    cfg = load_config(config_path)

    print("=" * 60)
    print("  uDev Automation Engine v0.1.0")
    print("=" * 60)
    print(f"  Knowledge root : {cfg['knowledge_root']}")
    print(f"  BrowserUI      : {cfg['browserui_endpoint']}")
    print(f"  Mode           : {'DRY-RUN' if args.dry_run else 'LIVE'}")
    if args.topic:
        print(f"  Topic filter   : {args.topic}")
    print()

    summary = run_pipeline(cfg, dry_run=args.dry_run, topic_filter=args.topic)

    print("\n" + "=" * 60)
    print("PIPELINE SUMMARY")
    print("=" * 60)
    print(f"  Files scanned   : {summary['scanned']}")
    print(f"  Files changed   : {summary['changed']}")
    print(f"  Refs scraped    : {summary['scraped']}")
    print(f"  Citations added : {summary['cited']}")
    print(f"  Notebooks gen   : {summary['notebooks']}")
    print(f"  Committed       : {summary['committed']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
