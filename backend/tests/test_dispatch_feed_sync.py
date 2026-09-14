"""Tests for Dispatch RSS/JSON Feeds, FeedServer Ingestion, and Offline Export."""
import json
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase

from app.api.dispatch_api import register_dispatch_routes
from app.services.dispatch_feed import dispatch_feed_service
from app.services.dispatch_offline import generate_standalone_html
from app.services.dispatch_store import dispatch_store
from app.services.feed_store import FeedServer


class TestDispatchFeedAndSync(AioHTTPTestCase):
    async def get_application(self):
        app = web.Application()
        register_dispatch_routes(app)
        return app

    def setUp(self):
        super().setUp()
        self.dispatch = dispatch_store.create_dispatch(
            title="Feed Demonstration Story",
            story_markdown="# Feed Step 1\nWelcome to the sovereign feed.\n---\n# Feed Step 2\n? [ ] Ready for RSS",
            lead_text="An RSS-syndicated calm invitation.",
            mode_default="card",
        )

    def test_rss_feed_generation(self):
        rss_xml = dispatch_feed_service.generate_rss_2_0("http://localhost:8484")
        assert "<rss version=\"2.0\"" in rss_xml
        assert "<title>Feed Demonstration Story</title>" in rss_xml
        assert f"/p/{self.dispatch['token']}" in rss_xml
        assert "<description>An RSS-syndicated calm invitation.</description>" in rss_xml

    def test_json_feed_generation(self):
        json_feed = dispatch_feed_service.generate_json_feed("http://localhost:8484")
        assert json_feed["version"] == "https://jsonfeed.org/version/1.1"
        assert len(json_feed["items"]) >= 1
        found = any(i["title"] == "Feed Demonstration Story" for i in json_feed["items"])
        assert found is True

    def test_feed_activity_pod_ingestion_on_rsvp(self):
        token = self.dispatch["token"]
        res = dispatch_store.submit_rsvp(
            token,
            {"name": "Grace Hopper", "answers": {"Ready for RSS": True}},
        )
        assert res["status"] == "success"

        # Check Activity Pod database
        feed_server = FeedServer()
        cursor = feed_server._conn.cursor()
        rows = cursor.execute(
            "SELECT * FROM user_activity WHERE source = 'dispatch' AND type = 'dispatch_rsvp_received'"
        ).fetchall()
        assert len(rows) >= 1
        last_rsvp = rows[-1]
        assert "Grace Hopper" in (last_rsvp["content"] or "")

    def test_standalone_html_generation(self):
        dispatch_id = self.dispatch["id"]
        standalone_html = generate_standalone_html(dispatch_id)
        assert "<!DOCTYPE html>" in standalone_html
        assert "Feed Demonstration Story" in standalone_html
        assert "Dispatched via sovereign uDos • 100% Offline" in standalone_html
        assert "downloadResponse()" in standalone_html

    async def test_api_feed_endpoints(self):
        # GET /api/dispatch/feed.xml
        resp_xml = await self.client.get("/api/dispatch/feed.xml")
        assert resp_xml.status == 200
        text_xml = await resp_xml.text()
        assert "<rss" in text_xml

        # GET /api/dispatch/feed.json
        resp_json = await self.client.get("/api/dispatch/feed.json")
        assert resp_json.status == 200
        data_json = await resp_json.json()
        assert "items" in data_json

        # GET /api/dispatch/motifs
        resp_motifs = await self.client.get("/api/dispatch/motifs")
        assert resp_motifs.status == 200
        data_motifs = await resp_motifs.json()
        assert "motifs" in data_motifs
        assert "zen_envelope" in data_motifs["motifs"]

    async def test_api_generate_bob_and_offline_export(self):
        # POST /api/dispatch/generate-bob
        bob_req = {
            "motif": "zen_envelope",
            "palette_id": "teletext_ceefax",
            "steps": 4,
            "delay_ms": 100,
        }
        resp_bob = await self.client.post("/api/dispatch/generate-bob", json=bob_req)
        assert resp_bob.status == 200
        data_bob = await resp_bob.json()
        assert data_bob["status"] == "ok"
        assert "asset_url" in data_bob
        assert data_bob["asset_name"].endswith(".gif")
        assert data_bob["gif_size_bytes"] > 0
        assert data_bob["gif_size_bytes"] <= 60 * 1024  # <= 60 KB

        # POST /api/dispatch/inbox/ingest
        token = self.dispatch["token"]
        inbound_payload = {
            "token": token,
            "name": "Alan Turing",
            "answers": {"Ready for RSS": True},
        }
        resp_ingest = await self.client.post("/api/dispatch/inbox/ingest", json=inbound_payload)
        assert resp_ingest.status == 200
        data_ingest = await resp_ingest.json()
        assert data_ingest["status"] == "success"

        # POST /api/dispatch/export-offline/{id}
        dispatch_id = self.dispatch["id"]
        resp_export = await self.client.post(f"/api/dispatch/export-offline/{dispatch_id}")
        assert resp_export.status == 200
        data_export = await resp_export.json()
        assert data_export["status"] == "ok"
        assert Path(data_export["standalone_html_path"]).exists()

