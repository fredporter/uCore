"""SnackMachine CLI — init, serve, index, spool commands."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="SnackMachine CLI")
    sub = parser.add_subparsers(dest="command")

    init_parser = sub.add_parser("init", help="Seed ~/.ucore/ with default configs")
    init_parser.add_argument("--force", action="store_true", help="Overwrite existing")

    sub.add_parser("serve", help="Start snackmachine daemon (requires uCore)")
    sub.add_parser("index", help="Rebuild library FTS5 index")
    sub.add_parser("spool-list", help="List recent spool entries")

    args = parser.parse_args()

    if args.command == "init":
        cmd_init(force=args.force)
    elif args.command == "serve":
        print("serve: run via uCore backend")
    elif args.command == "index":
        print("index: requires uCore backend running on port 8484")
    elif args.command == "spool-list":
        print("spool-list: requires uCore backend running")
    else:
        parser.print_help()


def cmd_init(force: bool = False) -> None:
    """Seed ~/.ucore/ with default snackmachine config."""
    data_dir = Path(os.environ.get("SNACKMACHINE_DATA_DIR", Path.home() / ".ucore"))
    dirs = [
        data_dir / "config" / "mcp-manifests",
        data_dir / "indices",
        data_dir / "knowledge",
        data_dir / "logs",
        data_dir / "snacks",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    manifest_path = data_dir / "config" / "mcp-manifests" / "knowledge.json"
    if manifest_path.exists() and not force:
        print(f"✓ {manifest_path} already exists (use --force to overwrite)")
    else:
        manifest_path.write_text(MCP_KNOWLEDGE_MANIFEST)
        print(f"✓ wrote {manifest_path}")

    spool_example = data_dir / "config" / "snackmachine.yaml"
    if spool_example.exists() and not force:
        print(f"✓ {spool_example} already exists")
    else:
        spool_example.write_text(SNACKMACHINE_CONFIG)
        print(f"✓ wrote {spool_example}")

    print(f"\n✅ snackmachine initialized at {data_dir}")
    print("   Run 'snackmachine index' to build the FTS5 search index.")
    print("   Drop snacks into ~/.ucore/snacks/ to auto-discover them.")


MCP_KNOWLEDGE_MANIFEST = json.dumps({
    "name": "mcp-knowledge-conduit",
    "version": "1.0.0",
    "description": "Knowledge conduit: vault search, AI-ranked retrieval, doclang",
    "tools": [
        "knowledge_search",
        "knowledge_ask",
        "knowledge_list_sources",
        "knowledge_extract_links",
        "knowledge_summarize",
        "knowledge_publish",
        "knowledge_query_memory",
    ],
    "transport": "http",
    "health_check": "/api/mcp/status",
    "protocolVersion": "0.1.0",
    "serverInfo": {"name": "SnackMachine Knowledge Conduit", "version": "1.0.0"},
}, indent=2)


SNACKMACHINE_CONFIG = """\
# SnackMachine config
# Drop .py snacks into ~/.ucore/snacks/ — they auto-discover

scheduler:
  interval: 60  # seconds between job checks
  jobs:
    - skill_id: backup
      time: "03:00"
    - skill_id: appflowy-sync
      time: "*/2 * * * *"  # every 2 hours

spool:
  dir: ~/.ucore/logs
  max_items: 1000
  max_days: 30

indices:
  dir: ~/.ucore/indices
  vault_layers:
    - user: ~/Vault
    - shared: ~/Shared
    - global: ~/Public/global-knowledge
    - public: ~/Public/doc-sites
    - code: ~/Code
"""
