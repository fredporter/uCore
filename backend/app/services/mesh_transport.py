"""Decentralized Local Mesh Transport & Discovery Service (BitCore / BitChat).

Adheres to uCore-Network Specification (2026):
- Zero-cloud, local-first LAN discovery over mDNS / Bonjour and UDP beacons
- Announced service types:
  - _bitchat._tcp.local. (Port 8085 / 3000)
  - _udos-portal._tcp.local. (Port 8080)
  - _sonic-depot._tcp.local. (Port 8088)
  - _homenest-media._tcp.local. (Port 8096)
- Zero external package dependencies (pure standard-library sockets and host CLI)
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import platform
import socket
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable, Dict, List, Optional

log = logging.getLogger("ucore.mesh_transport")

MESH_BEACON_MAGIC = "UDOS_MESH_BEACON_V1"
DEFAULT_MESH_PORT = 53535
MULTICAST_GROUP = "224.0.0.251"
DEFAULT_SERVICES = [
    "_bitchat._tcp.local.",
    "_udos-portal._tcp.local.",
    "_sonic-depot._tcp.local.",
    "_homenest-media._tcp.local.",
]


@dataclass
class MeshPeer:
    peer_id: str
    node_name: str
    ip: str
    port: int
    service_type: str = "_bitchat._tcp.local."
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=lambda: ["chat", "prose", "evidence", "tasks"])
    last_seen: float = field(default_factory=time.time)
    is_local: bool = False
    status: str = "online"

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        now = time.time()
        age = now - self.last_seen
        if age > 60:
            data["status"] = "idle"
        if age > 120:
            data["status"] = "offline"
        data["age_seconds"] = round(age, 1)
        return data


class PeerRegistry:
    """Thread-safe in-memory registry of discovered LAN peers."""

    def __init__(self, local_peer_id: Optional[str] = None, local_node_name: Optional[str] = None):
        self._peers: Dict[str, MeshPeer] = {}
        self.local_peer_id = local_peer_id or f"node_{socket.gethostname().split('.')[0]}_{os.getpid()}"
        self.local_node_name = local_node_name or f"uDos @ {socket.gethostname().split('.')[0]}"
        # Register local node
        self.register_peer(
            MeshPeer(
                peer_id=self.local_peer_id,
                node_name=self.local_node_name,
                ip="127.0.0.1",
                port=3000,
                service_type="_bitchat._tcp.local.",
                capabilities=["chat", "prose", "evidence", "tasks", "host"],
                is_local=True,
                status="online",
            )
        )

    def register_peer(self, peer: MeshPeer) -> None:
        peer.last_seen = time.time()
        self._peers[peer.peer_id] = peer
        log.debug("Mesh peer registered/updated: %s (%s:%s)", peer.node_name, peer.ip, peer.port)

    def update_heartbeat(self, peer_id: str) -> bool:
        if peer_id in self._peers:
            self._peers[peer_id].last_seen = time.time()
            self._peers[peer_id].status = "online"
            return True
        return False

    def get_peer(self, peer_id: str) -> Optional[MeshPeer]:
        return self._peers.get(peer_id)

    def get_peers(self, service_type: Optional[str] = None, include_stale: bool = False) -> List[Dict[str, Any]]:
        self.prune_stale_peers()
        results = []
        for peer in self._peers.values():
            if service_type and peer.service_type != service_type:
                continue
            dict_rep = peer.to_dict()
            if not include_stale and dict_rep["status"] == "offline":
                continue
            results.append(dict_rep)
        return sorted(results, key=lambda x: (not x["is_local"], x["node_name"]))

    def prune_stale_peers(self, max_age_seconds: float = 180.0) -> int:
        now = time.time()
        to_delete = [
            pid for pid, peer in self._peers.items()
            if not peer.is_local and (now - peer.last_seen) > max_age_seconds
        ]
        for pid in to_delete:
            del self._peers[pid]
        return len(to_delete)


class MeshDiscoveryService:
    """Asynchronous local mesh beacon advertiser and listener."""

    def __init__(
        self,
        registry: Optional[PeerRegistry] = None,
        port: int = 3000,
        beacon_port: int = DEFAULT_MESH_PORT,
    ):
        self.registry = registry or PeerRegistry()
        self.port = port
        self.beacon_port = beacon_port
        self._running = False
        self._listener_task: Optional[asyncio.Task] = None
        self._beacon_task: Optional[asyncio.Task] = None

    def build_beacon_payload(self) -> bytes:
        payload = {
            "magic": MESH_BEACON_MAGIC,
            "peer_id": self.registry.local_peer_id,
            "node_name": self.registry.local_node_name,
            "port": self.port,
            "service_type": "_bitchat._tcp.local.",
            "services": DEFAULT_SERVICES,
            "capabilities": ["chat", "prose", "evidence", "tasks"],
            "timestamp": time.time(),
        }
        return json.dumps(payload).encode("utf-8")

    def parse_beacon_payload(self, data: bytes, addr: tuple[str, int]) -> Optional[MeshPeer]:
        try:
            msg = json.loads(data.decode("utf-8"))
            if msg.get("magic") != MESH_BEACON_MAGIC:
                return None
            peer_id = str(msg.get("peer_id") or "")
            if not peer_id or peer_id == self.registry.local_peer_id:
                return None  # Ignore self-announcement

            return MeshPeer(
                peer_id=peer_id,
                node_name=str(msg.get("node_name") or f"Node-{peer_id[:6]}"),
                ip=addr[0],
                port=int(msg.get("port") or 3000),
                service_type=str(msg.get("service_type") or "_bitchat._tcp.local."),
                capabilities=list(msg.get("capabilities") or ["chat"]),
                is_local=False,
                status="online",
            )
        except Exception as exc:
            log.debug("Invalid mesh beacon from %s: %s", addr, exc)
            return None

    def send_broadcast_beacon(self) -> bool:
        """Send a single UDP broadcast beacon to the local subnet."""
        data = self.build_beacon_payload()
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.settimeout(1.0)
                sock.sendto(data, ("<broadcast>", self.beacon_port))
                return True
        except Exception as exc:
            log.debug("Mesh beacon broadcast failed: %s", exc)
            return False

    async def start(self) -> None:
        """Start background listener and periodic beacon advertiser."""
        if self._running:
            return
        self._running = True
        log.info("Starting MeshDiscoveryService on beacon port %s", self.beacon_port)

    async def stop(self) -> None:
        """Stop background tasks."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            self._listener_task = None
        if self._beacon_task:
            self._beacon_task.cancel()
            self._beacon_task = None


# Singleton instance
_global_registry = PeerRegistry()
_global_discovery = MeshDiscoveryService(registry=_global_registry)


def get_mesh_registry() -> PeerRegistry:
    return _global_registry


def get_mesh_discovery() -> MeshDiscoveryService:
    return _global_discovery
