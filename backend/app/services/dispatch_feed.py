"""Sovereign Dispatch Feed Generator.

Generates decentralized RSS 2.0 XML and JSON Feed v1.1 formats for all
published dispatches and binder editions, including GIF enclosures and Prose descriptions.
Saves local feed files under ~/Vault/feeds/dispatches.xml.
"""
from __future__ import annotations

import email.utils
import html
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.settings import settings
from app.services.dispatch_store import dispatch_store

log = logging.getLogger("ucore.dispatch_feed")


class DispatchFeedService:
    """Syndication engine publishing sovereign dispatches as RSS & JSON feeds."""

    def __init__(self, feeds_dir: Optional[Path] = None):
        self.feeds_dir = feeds_dir or (settings.vault_root / "feeds")
        self.feeds_dir.mkdir(parents=True, exist_ok=True)

    def generate_rss_2_0(self, host_url: str = "") -> str:
        """Generate standard RSS 2.0 XML string."""
        dispatches = dispatch_store.list_dispatches()
        now_rfc822 = email.utils.format_datetime(datetime.now(timezone.utc))

        items_xml = []
        for d in dispatches:
            if d.get("status") not in ("active", "published"):
                continue

            token = d.get("token", "")
            title = html.escape(d.get("title", "Untitled Dispatch"))
            lead = html.escape(d.get("lead_text", ""))
            created_ts = d.get("created_at", 0)
            item_dt = datetime.fromtimestamp(created_ts, timezone.utc) if created_ts else datetime.now(timezone.utc)
            item_rfc822 = email.utils.format_datetime(item_dt)

            item_link = f"{host_url}/p/{token}" if token else host_url
            enclosure_xml = ""
            hero_asset = d.get("hero_asset")
            if hero_asset:
                full_asset_url = f"{host_url}{hero_asset}" if hero_asset.startswith("/") else hero_asset
                enclosure_xml = f'      <enclosure url="{html.escape(full_asset_url)}" length="1024" type="image/gif" />\n'

            item_block = f"""    <item>
      <title>{title}</title>
      <link>{item_link}</link>
      <guid isPermaLink="false">{d.get('id', token)}</guid>
      <pubDate>{item_rfc822}</pubDate>
      <description>{lead}</description>
{enclosure_xml}    </item>"""
            items_xml.append(item_block)

        items_joined = "\n".join(items_xml)
        rss_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>uDos Sovereign Dispatches</title>
    <link>{host_url}/api/dispatch/feed.xml</link>
    <description>Sovereign invitations, interactive stories, and binder dispatches.</description>
    <language>en</language>
    <lastBuildDate>{now_rfc822}</lastBuildDate>
    <atom:link href="{host_url}/api/dispatch/feed.xml" rel="self" type="application/rss+xml" />
{items_joined}
  </channel>
</rss>"""
        return rss_content

    def generate_json_feed(self, host_url: str = "") -> Dict[str, Any]:
        """Generate modern JSON Feed v1.1 format."""
        dispatches = dispatch_store.list_dispatches()
        items = []

        for d in dispatches:
            if d.get("status") not in ("active", "published"):
                continue

            token = d.get("token", "")
            created_iso = d.get("created_iso", datetime.now(timezone.utc).isoformat())
            hero_asset = d.get("hero_asset")
            image_url = f"{host_url}{hero_asset}" if hero_asset and hero_asset.startswith("/") else hero_asset

            items.append({
                "id": d.get("id", token),
                "url": f"{host_url}/p/{token}" if token else host_url,
                "title": d.get("title", "Untitled Dispatch"),
                "summary": d.get("lead_text", ""),
                "date_published": created_iso,
                "image": image_url,
            })

        return {
            "version": "https://jsonfeed.org/version/1.1",
            "title": "uDos Sovereign Dispatches",
            "home_page_url": f"{host_url}/p/",
            "feed_url": f"{host_url}/api/dispatch/feed.json",
            "description": "Sovereign invitations, interactive stories, and binder dispatches.",
            "items": items,
        }

    def sync_to_vault(self, host_url: str = "") -> Dict[str, str]:
        """Persist generated RSS and JSON feeds into ~/Vault/feeds/."""
        rss_xml = self.generate_rss_2_0(host_url)
        json_feed = self.generate_json_feed(host_url)

        rss_path = self.feeds_dir / "dispatches.xml"
        json_path = self.feeds_dir / "dispatches.json"

        rss_path.write_text(rss_xml, encoding="utf-8")
        json_path.write_text(json.dumps(json_feed, indent=2), encoding="utf-8")

        log.info("Syndicated dispatch feeds written to %s and %s", rss_path, json_path)
        return {
            "rss_path": str(rss_path),
            "json_path": str(json_path),
        }


dispatch_feed_service = DispatchFeedService()
