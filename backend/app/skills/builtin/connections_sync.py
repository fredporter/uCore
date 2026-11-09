"""Run one already-enabled, profile-owned connection through the shared sync engine.

Owner: uCore connectors / uFlow orchestration. No new process or schedule.
Budget: one connection, 90s worker budget + one bounded request. Removal: remove
this catalogue entry and workflow steps referencing connections_sync; records stay.
"""

from app.services.identity import get_full_identity
from app.services.snackbar_sync import sync_connection
from app.skills.base import BaseSkill, SkillMeta, SkillParam


class ConnectionsSync(BaseSkill):
    meta = SkillMeta(
        id="connections_sync",
        name="Sync connection",
        category="workflow",
        timeout=150,
        description="Sync a previously enabled Apple or Google connection using its chosen scope",
        params=[
            SkillParam(
                name="connection_id",
                required=True,
                description="A connection owned by the current profile",
            )
        ],
    )

    async def run(self, connection_id="", **kwargs):
        identity = get_full_identity()
        if not identity.get("authenticated") or not identity.get("active_profile_id"):
            return {"success": False, "error": "Choose a user profile"}
        result = await sync_connection(identity["active_profile_id"], connection_id)
        return {"success": result["state"] == "connected", **result}
