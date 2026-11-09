"""Snackbar sync coordination over the existing scoped connection engine.

No extra scheduler, process, environment or state store. Health remains in the
profile-owned connection store; the existing Snackbar maintenance loop owns polls.
"""

from app.services.connections.engine import SyncEngine


async def sync_connection(profile, connection_id, *, manual=False, store=None):
    return await SyncEngine(store).sync(profile, connection_id, manual=manual)
