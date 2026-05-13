# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import AutomationDraftInput
from discord_mcp_platform.services.automation_service import AutomationService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.automation.draft",
            description="Draft an automation from a natural language description.",
            inputSchema=AutomationDraftInput.model_json_schema(),
        ),
    ]


def get_handler(
    automation_service: AutomationService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name != "discord.automation.draft":
            return None
        input_data = AutomationDraftInput.model_validate(arguments)
        result = await automation_service.draft(input_data)
        await audit.record(
            workspace_id="system",
            action="discord.automation.draft",
            guild_id=input_data.guild_id,
            details={"description_length": len(input_data.description)},
        )
        return [TextContent(type="text", text=result.model_dump_json())]

    return handle
