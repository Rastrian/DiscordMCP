# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    GuildListInput,
    GuildGetInput,
    GuildModifyInput,
    GuildIncidentActionsInput,
)
from discord_mcp_platform.services.guild_service import GuildService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.guild.list",
            description="List Discord guilds the bot is installed in.",
            inputSchema=GuildListInput.model_json_schema(),
        ),
        Tool(
            name="discord.guild.get",
            description="Get a Discord guild by ID.",
            inputSchema=GuildGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.guild.modify",
            description="Modify a Discord guild. Defaults to dry-run mode.",
            inputSchema=GuildModifyInput.model_json_schema(),
        ),
        Tool(
            name="discord.guild.incident_actions",
            description=(
                "Set guild incident actions (server lockdown): temporarily disable "
                "invites and/or DMs for the whole guild until the given ISO 8601 "
                "timestamps. Discord allows at most 24h ahead; pass null to "
                "re-enable. Defaults to dry-run mode."
            ),
            inputSchema=GuildIncidentActionsInput.model_json_schema(),
        ),
    ]


def get_handler(
    guild_service: GuildService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.guild.list":
            input_data = GuildListInput.model_validate(arguments)
            result = await guild_service.list_guilds(input_data, scopes="guild:read")
            await audit.record(
                workspace_id="system",
                action="discord.guild.list",
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        if name == "discord.guild.get":
            input_data = GuildGetInput.model_validate(arguments)
            result = await guild_service.get_guild(input_data.guild_id, scopes="guild:read")
            await audit.record(
                workspace_id="system",
                action="discord.guild.get",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.guild.modify":
            input_data = GuildModifyInput.model_validate(arguments)
            result = await guild_service.modify_guild(
                input_data.guild_id,
                scopes="guild:write",
                name=input_data.name,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.guild.modify",
                guild_id=input_data.guild_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.guild.incident_actions":
            input_data = GuildIncidentActionsInput.model_validate(arguments)
            result = await guild_service.set_incident_actions(
                input_data.guild_id,
                input_data.invites_disabled_until,
                input_data.dms_disabled_until,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.guild.incident_actions",
                guild_id=input_data.guild_id,
                details={
                    "dry_run": input_data.dry_run,
                    "invites_disabled_until": input_data.invites_disabled_until,
                    "dms_disabled_until": input_data.dms_disabled_until,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
