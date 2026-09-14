"""Tests for Decentralized Mesh Transport & Discovery Service (BitCore / BitChat).

Verifies:
- PeerRegistry: local node registration, peer registration, heartbeat update, pruning stale peers
- MeshDiscoveryService: beacon payload format, beacon parsing, loopback ignore
- Mesh API: GET /api/network/mesh/peers, POST /api/network/mesh/announce
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from app.api.bitchat_api import register_bitchat_routes
from app.services.mesh_transport import (
    MESH_BEACON_MAGIC,
    MeshDiscoveryService,
    MeshPeer,
    PeerRegistry,
)


def test_peer_registry_lifecycle():
    """Verify local registration, peer registration, status transitions, and pruning."""
    registry = PeerRegistry(local_peer_id="test_node_local", local_node_name="Local uDos")
    assert registry.local_peer_id == "test_node_local"

    peers = registry.get_peers()
    assert len(peers) == 1
    assert peers[0]["peer_id"] == "test_node_local"
    assert peers[0]["is_local"] is True
    assert peers[0]["status"] == "online"

    # Register remote peer
    remote_peer = MeshPeer(
        peer_id="remote_node_1",
        node_name="Living Room Sonic",
        ip="192.168.1.50",
        port=3000,
        service_type="_bitchat._tcp.local.",
        capabilities=["chat", "prose"],
        last_seen=time.time(),
        is_local=False,
    )
    registry.register_peer(remote_peer)

    peers = registry.get_peers()
    assert len(peers) == 2
    remote = next(p for p in peers if p["peer_id"] == "remote_node_1")
    assert remote["node_name"] == "Living Room Sonic"
    assert remote["status"] == "online"

    # Test idle and offline status based on age
    remote_peer.last_seen = time.time() - 70  # 70s ago -> idle
    assert remote_peer.to_dict()["status"] == "idle"

    remote_peer.last_seen = time.time() - 130  # 130s ago -> offline
    assert remote_peer.to_dict()["status"] == "offline"

    # Heartbeat revives status to online
    registry.update_heartbeat("remote_node_1")
    assert registry.get_peer("remote_node_1").status == "online"

    # Stale peer pruning (older than 180s)
    remote_peer.last_seen = time.time() - 200
    pruned = registry.prune_stale_peers(max_age_seconds=180.0)
    assert pruned == 1
    assert registry.get_peer("remote_node_1") is None
    # Local peer should never be pruned
    assert registry.get_peer("test_node_local") is not None


def test_discovery_beacon_payload_and_parse():
    """Verify beacon serialization and parsing."""
    registry = PeerRegistry(local_peer_id="beacon_tester", local_node_name="Tester Node")
    discovery = MeshDiscoveryService(registry=registry, port=3000)

    raw_payload = discovery.build_beacon_payload()
    data = json.loads(raw_payload.decode("utf-8"))
    assert data["magic"] == MESH_BEACON_MAGIC
    assert data["peer_id"] == "beacon_tester"
    assert data["node_name"] == "Tester Node"
    assert "_bitchat._tcp.local." in data["services"]

    # Parsing valid incoming beacon from remote IP
    remote_beacon = json.dumps({
        "magic": MESH_BEACON_MAGIC,
        "peer_id": "remote_beacon_99",
        "node_name": "Studio Workshop Kiosk",
        "port": 3000,
        "service_type": "_bitchat._tcp.local.",
        "capabilities": ["chat", "tasks"],
        "timestamp": time.time(),
    }).encode("utf-8")

    parsed = discovery.parse_beacon_payload(remote_beacon, ("192.168.1.120", 53535))
    assert parsed is not None
    assert parsed.peer_id == "remote_beacon_99"
    assert parsed.node_name == "Studio Workshop Kiosk"
    assert parsed.ip == "192.168.1.120"
    assert parsed.is_local is False

    # Ignore self-beacon
    self_beacon = discovery.build_beacon_payload()
    parsed_self = discovery.parse_beacon_payload(self_beacon, ("127.0.0.1", 53535))
    assert parsed_self is None

    # Ignore non-matching magic
    invalid_beacon = json.dumps({"magic": "OTHER_PROTOCOL"}).encode("utf-8")
    assert discovery.parse_beacon_payload(invalid_beacon, ("10.0.0.1", 53535)) is None


@pytest.fixture
async def mesh_client(tmp_path: Path):
    """Create test client for mesh API."""
    app = web.Application()
    register_bitchat_routes(app)
    async with TestClient(TestServer(app)) as client:
        yield client


@pytest.mark.asyncio
async def test_mesh_api_peers_and_announce(mesh_client):
    """Verify GET /api/network/mesh/peers and POST /api/network/mesh/announce."""
    resp = await mesh_client.get("/api/network/mesh/peers")
    assert resp.status == 200
    data = await resp.json()
    assert data["status"] == "ok"
    assert "peers" in data
    assert len(data["peers"]) >= 1

    resp_announce = await mesh_client.post("/api/network/mesh/announce")
    assert resp_announce.status == 200
    data_ann = await resp_announce.json()
    assert data_ann["status"] == "ok"
    assert "peer_id" in data_ann
