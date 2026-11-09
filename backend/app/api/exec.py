"""Compatibility endpoint for the retired generic shell execution API.

User operations belong to registered skills, task actions and managed apps.
External development tools own host shell and repository commands.
"""
from __future__ import annotations

from aiohttp import web


async def handle_exec(request: web.Request) -> web.Response:
    """Reject generic shell execution without parsing or running a command."""
    return web.json_response({
        "error": "generic_execution_retired",
        "message": "Use a registered skill or task action. Host shell commands belong in external developer tools.",
        "owner": "external-development",
    }, status=410)
