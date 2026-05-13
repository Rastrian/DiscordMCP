# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from mcp.types import Tool, TextContent

from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.audit.list",
            description="List audit events for a workspace, optionally filtered by guild or action type.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "Workspace ID to query audit events for",
                    },
                    "guild_id": {"type": "string", "description": "Optional guild ID filter"},
                    "action": {"type": "string", "description": "Optional action type filter"},
                    "limit": {
                        "type": "integer",
                        "description": "Max events to return (default 50, max 200)",
                        "default": 50,
                    },
                },
                "required": ["workspace_id"],
            },
        ),
    ]


def get_handler(
    audit_service: AuditService,
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name != "discord.audit.list":
            return None

        workspace_id = arguments.get("workspace_id", "system")
        guild_id = arguments.get("guild_id")
        action = arguments.get("action")
        limit = min(arguments.get("limit", 50), 200)

        events = await audit_service.list_events(
            workspace_id=workspace_id,
            guild_id=guild_id,
            action=action,
            limit=limit,
        )
        return [TextContent(type="text", text=json.dumps({"events": events, "count": len(events)}))]

    return handle
