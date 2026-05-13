# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import ThreadCreateInput
from discord_mcp_platform.services.thread_service import ThreadService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.thread.create",
            description="Create a thread in a Discord channel. Defaults to dry-run mode.",
            inputSchema=ThreadCreateInput.model_json_schema(),
        ),
    ]


def get_handler(
    thread_service: ThreadService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name != "discord.thread.create":
            return None
        input_data = ThreadCreateInput.model_validate(arguments)
        result = await thread_service.create(input_data, scopes="thread:write")
        await audit.record(
            workspace_id="system",
            action="discord.thread.create",
            guild_id=input_data.guild_id,
            channel_id=input_data.channel_id,
            details={"dry_run": input_data.dry_run, "name": input_data.name},
        )
        return [TextContent(type="text", text=result.model_dump_json())]

    return handle
