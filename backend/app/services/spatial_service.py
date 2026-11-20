"""Spatial Service — NFC marker resolution, waypoint tracking, and peer handshake.

Fulfills LOCAL_FIRST_LIBRARY_DELIVERY specifications for offline spatial awareness:
- MarkerEnvelope { version, marker_id }
- TapObservation { event_id, marker_payload, observed_at, simulated_position? }
- TapReceipt { event_id, outcome, waypoint_ref?, authorised_resource_refs? }
- PeerHandshake { challenge, response, nonce, peer_id, audience, expiry }
- Replay-safe receipt store keyed by profile_id + event_id
"""
from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import sqlite3
from contextlib import closing
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.core.settings import settings

log = logging.getLogger("ucore.spatial_service")

class SpatialService:
    """Fixture-backed spatial lookup and durable tap receipts."""

    def __init__(self, fixture_path: Path | None = None, receipt_path: Path | None = None) -> None:
        self.fixture_path = fixture_path or settings.shared_vault_root / "fixtures" / "fixture.json"
        self.receipt_path = receipt_path or settings.udos_home / "data" / "spatial_taps.sqlite3"
        self._issued_challenges: dict[str, tuple[str, str, float]] = {}
        # Nonce cache for peer handshakes: nonce -> consumed_timestamp
        self._consumed_nonces: dict[str, float] = {}
        # Revoked peers set
        self._revoked_peers: set[str] = set()

    def load_fixture(self) -> dict[str, Any]:
        if not self.fixture_path.is_file():
            return {}
        try:
            data = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            log.warning("Could not read spatial fixture: %s", exc)
            return {}

    def resolve_tap(
        self,
        profile_id: str,
        event_id: str,
        marker_payload: dict[str, Any],
        simulated_position: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Process a simulated NFC tap observation idempotently."""
        fixture = self.load_fixture()
        tap = fixture.get("tap", {})
        waypoint = fixture.get("fictional_place", {})
        binder = fixture.get("binder", {})
        denied = {
            "event_id": event_id,
            "outcome": "unauthorised",
            "waypoint_ref": None,
            "authorised_resource_refs": None,
        }
        if (
            not all(isinstance(record, dict) for record in (tap, waypoint, binder))
            or not profile_id or profile_id in {"anonymous", "signed-out"}
            or not self._visible(fixture, profile_id)
            or not self._visible(waypoint, profile_id, inherit=fixture)
            or tap.get("marker_envelope") != marker_payload
            or not tap.get("waypoint_ref")
            or tap["waypoint_ref"] != waypoint.get("waypoint_ref")
        ):
            return denied

        # This simulator resolves only fixture-owned resources with a known schema.
        # Arbitrary references cannot be resolved through this fixture.
        binder_id = binder.get("binder_id")
        binder_ref = f"urn:uds:fixture:generic:{binder_id}" if isinstance(binder_id, str) and binder_id else None
        declared_refs = tap.get("authorised_resources")
        resources = (
            [binder_ref] if binder_ref and isinstance(declared_refs, list) and binder_ref in declared_refs
            and self._visible(binder, profile_id, inherit=fixture) else []
        )

        processed_at = datetime.now(UTC).isoformat()
        self.receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.receipt_path)) as db, db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tap_receipts (
                    profile TEXT NOT NULL, event TEXT NOT NULL, marker TEXT NOT NULL,
                    processed_at TEXT NOT NULL, PRIMARY KEY (profile, event)
                )
            """)
            marker = marker_payload["marker_id"]
            result = db.execute(
                "INSERT OR IGNORE INTO tap_receipts VALUES (?, ?, ?, ?)",
                (profile_id, event_id, marker, processed_at),
            )
            replayed = result.rowcount == 0
            if replayed:
                prior_marker, processed_at = db.execute(
                    "SELECT marker, processed_at FROM tap_receipts WHERE profile = ? AND event = ?",
                    (profile_id, event_id),
                ).fetchone()
                if prior_marker != marker:
                    return denied

        return {
            "event_id": event_id,
            "outcome": "success",
            "waypoint_ref": tap["waypoint_ref"],
            "authorised_resource_refs": resources,
            "claimed_position": simulated_position,
            "registered_position": waypoint.get("coordinates"),
            "processed_at": processed_at,
            "replayed": replayed,
        }

    @staticmethod
    def _visible(record: dict[str, Any], profile_id: str, *, inherit: dict | None = None) -> bool:
        parent = inherit or {}
        visibility = record.get("visibility", parent.get("visibility"))
        owner = record.get("owner_profile_id", parent.get("owner_profile_id"))
        return visibility == "public" or (visibility == "private" and owner == profile_id)

    # ── Peer Handshake ──────────────────────────────────────────────────

    def generate_handshake_challenge(self, peer_id: str, audience: str = "ucore-spatial-service") -> dict[str, Any]:
        """Generate a fresh nonced challenge with 60s TTL."""
        now = time.time()
        self._issued_challenges = {
            token: issued for token, issued in self._issued_challenges.items() if issued[2] >= now
        }
        self._consumed_nonces = {
            token: until for token, until in self._consumed_nonces.items() if until >= now
        }
        nonce = secrets.token_hex(16)
        expiry = now + 60.0
        self._issued_challenges[nonce] = (peer_id, audience, expiry)
        return {
            "peer_id": peer_id,
            "audience": audience,
            "nonce": nonce,
            "expiry": expiry,
            "protocol_version": "1.0",
        }

    def verify_handshake_response(
        self,
        peer_id: str,
        audience: str,
        nonce: str,
        expiry: float,
        signature: str,
        protocol_version: str = "1.0",
    ) -> dict[str, Any]:
        """Verify peer response challenge, single-use nonce, audience, expiry, and revocation."""
        if peer_id in self._revoked_peers:
            return {"outcome": "denied", "reason": "peer_revoked"}

        if time.time() > expiry:
            return {"outcome": "denied", "reason": "expired"}

        if nonce in self._consumed_nonces:
            return {"outcome": "denied", "reason": "nonce_replayed"}

        fixture = self.load_fixture()
        peer_cfg = fixture.get("peer_handshake", {})
        if not isinstance(peer_cfg, dict):
            return {"outcome": "denied", "reason": "unsupported_peer"}
        expected_peer = peer_cfg.get("test_peer_id")
        expected_audience = peer_cfg.get("audience", "ucore-spatial-service")
        secret = peer_cfg.get("pre_enrolled_secret")

        if peer_id != expected_peer or audience != expected_audience:
            return {"outcome": "denied", "reason": "wrong_audience_or_peer"}

        if not isinstance(secret, str) or not secret or protocol_version != peer_cfg.get("protocol_version", "1.0"):
            return {"outcome": "denied", "reason": "unsupported_peer"}

        if self._issued_challenges.get(nonce) != (peer_id, audience, expiry):
            return {"outcome": "denied", "reason": "unknown_challenge"}

        # Expected signature: HMAC-SHA256(secret, f"{protocol_version}:{peer_id}:{audience}:{nonce}:{int(expiry)}")
        expected_msg = f"{protocol_version}:{peer_id}:{audience}:{nonce}:{int(expiry)}".encode("utf-8")
        expected_sig = hmac.new(secret.encode("utf-8"), expected_msg, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return {"outcome": "denied", "reason": "invalid_signature"}

        # Consume nonce
        del self._issued_challenges[nonce]
        self._consumed_nonces[nonce] = expiry

        return {
            "outcome": "accepted",
            "peer_id": peer_id,
            "audience": audience,
            "nonce": nonce,
        }

    def revoke_peer(self, peer_id: str) -> None:
        self._revoked_peers.add(peer_id)


_spatial_service: SpatialService | None = None


def get_spatial_service() -> SpatialService:
    global _spatial_service
    if _spatial_service is None:
        _spatial_service = SpatialService()
    return _spatial_service
