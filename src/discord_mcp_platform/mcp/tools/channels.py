# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    ChannelListInput,
    ChannelGetInput,
    ChannelCreateInput,
    ChannelEditInput,
    ChannelDeleteInput,
    ChannelPermissionsEditInput,
    ChannelPermissionsDeleteInput,
)
from discord_mcp_platform.services.channel_service import ChannelService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.channel.list",
            description="List channels in a Discord guild.",
            inputSchema=ChannelListInput.model_json_schema(),
        ),
        Tool(
            name="discord.channel.get",
            description="Get a Discord channel by ID.",
            inputSchema=ChannelGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.channel.create",
            description="Create a channel in a Discord guild. Defaults to dry-run mode.",
            inputSchema=ChannelCreateInput.model_json_schema(),
        ),
        Tool(
            name="discord.channel.edit",
            description="Edit a channel in a Discord guild. Defaults to dry-run mode.",
            inputSchema=ChannelEditInput.model_json_schema(),
        ),
        Tool(
            name="discord.channel.delete",
            description="Delete a channel from a Discord guild. Defaults to dry-run mode.",
            inputSchema=ChannelDeleteInput.model_json_schema(),
        ),
        Tool(
            name="discord.channel.edit_permissions",
            description="Edit permission overwrites for a channel. Defaults to dry-run mode.",
            inputSchema=ChannelPermissionsEditInput.model_json_schema(),
        ),
        Tool(
            name="discord.channel.delete_permissions",
            description="Delete a permission overwrite for a channel. Defaults to dry-run mode.",
            inputSchema=ChannelPermissionsDeleteInput.model_json_schema(),
        ),
    ]


def get_handler(
    channel_service: ChannelService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.channel.list":
            input_data = ChannelListInput.model_validate(arguments)
            result = await channel_service.list_channels(input_data, scopes="channel:read")
            await audit.record(
                workspace_id="system",
                action="discord.channel.list",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        if name == "discord.channel.get":
            input_data = ChannelGetInput.model_validate(arguments)
            result = await channel_service.get_channel(input_data.channel_id, scopes="channel:read")
            await audit.record(
                workspace_id="system",
                action="discord.channel.get",
                channel_id=input_data.channel_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.channel.create":
            input_data = ChannelCreateInput.model_validate(arguments)
            result = await channel_service.create_channel(
                input_data.guild_id,
                input_data.name,
                scopes="channel:write",
                channel_type=input_data.channel_type,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
                parent_id=input_data.parent_id,
            )
            await audit.record(
                workspace_id="system",
                action="discord.channel.create",
                guild_id=input_data.guild_id,
                details={"dry_run": input_data.dry_run, "name": input_data.name},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.channel.edit":
            input_data = ChannelEditInput.model_validate(arguments)
            result = await channel_service.edit_channel(
                input_data.guild_id,
                input_data.channel_id,
                scopes="channel:write",
                name=input_data.name,
                topic=input_data.topic,
                parent_id=input_data.parent_id,
                nsfw=input_data.nsfw,
                rate_limit_per_user=input_data.rate_limit_per_user,
                bitrate=input_data.bitrate,
                user_limit=input_data.user_limit,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.channel.edit",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.channel.delete":
            input_data = ChannelDeleteInput.model_validate(arguments)
            result = await channel_service.delete_channel(
                input_data.channel_id,
                input_data.guild_id,
                scopes="channel:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.channel.delete",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.channel.edit_permissions":
            input_data = ChannelPermissionsEditInput.model_validate(arguments)
            result = await channel_service.edit_permissions(
                input_data.guild_id,
                input_data.channel_id,
                input_data.overwrite_id,
                input_data.overwrite_type,
                input_data.allow,
                input_data.deny,
                scopes="channel:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.channel.edit_permissions",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                target_id=input_data.overwrite_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.channel.delete_permissions":
            input_data = ChannelPermissionsDeleteInput.model_validate(arguments)
            result = await channel_service.delete_permissions(
                input_data.guild_id,
                input_data.channel_id,
                input_data.overwrite_id,
                scopes="channel:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.channel.delete_permissions",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                target_id=input_data.overwrite_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
