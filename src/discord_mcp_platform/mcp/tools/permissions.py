# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    PermissionsChannelMemberInput,
    PermissionsChannelRoleInput,
    PermissionsGuildMemberInput,
    PermissionsGuildRoleInput,
)
from discord_mcp_platform.services.permission_query_service import PermissionQueryService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.permissions.get_guild_member",
            description="Get the computed permissions of a guild member.",
            inputSchema=PermissionsGuildMemberInput.model_json_schema(),
        ),
        Tool(
            name="discord.permissions.get_guild_role",
            description="Get the computed permissions of a guild role.",
            inputSchema=PermissionsGuildRoleInput.model_json_schema(),
        ),
        Tool(
            name="discord.permissions.get_channel_member",
            description="Get the computed permissions of a member in a channel.",
            inputSchema=PermissionsChannelMemberInput.model_json_schema(),
        ),
        Tool(
            name="discord.permissions.get_channel_role",
            description="Get the computed permissions of a role in a channel.",
            inputSchema=PermissionsChannelRoleInput.model_json_schema(),
        ),
    ]


def get_handler(
    permission_service: PermissionQueryService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.permissions.get_guild_member":
            input_data = PermissionsGuildMemberInput.model_validate(arguments)
            result = await permission_service.get_guild_member_permissions(
                input_data.guild_id, input_data.user_id, scopes="guild:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.permissions.get_guild_member",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.permissions.get_guild_role":
            input_data = PermissionsGuildRoleInput.model_validate(arguments)
            result = await permission_service.get_guild_role_permissions(
                input_data.guild_id, input_data.role_id, scopes="guild:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.permissions.get_guild_role",
                guild_id=input_data.guild_id,
                target_id=input_data.role_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.permissions.get_channel_member":
            input_data = PermissionsChannelMemberInput.model_validate(arguments)
            result = await permission_service.get_channel_member_permissions(
                input_data.channel_id, input_data.user_id, scopes="channel:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.permissions.get_channel_member",
                channel_id=input_data.channel_id,
                target_id=input_data.user_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.permissions.get_channel_role":
            input_data = PermissionsChannelRoleInput.model_validate(arguments)
            result = await permission_service.get_channel_role_permissions(
                input_data.channel_id, input_data.role_id, scopes="channel:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.permissions.get_channel_role",
                channel_id=input_data.channel_id,
                target_id=input_data.role_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
