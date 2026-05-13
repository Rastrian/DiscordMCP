# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    MemberGetInput,
    MemberListInput,
    MemberKickInput,
    MemberBanInput,
    MemberTimeoutInput,
    MemberUnbanInput,
)
from discord_mcp_platform.services.member_service import MemberService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.member.get",
            description="Get a member of a Discord guild.",
            inputSchema=MemberGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.member.list",
            description="List members of a Discord guild.",
            inputSchema=MemberListInput.model_json_schema(),
        ),
        Tool(
            name="discord.member.kick",
            description="Kick a member from a Discord guild. Defaults to dry-run mode.",
            inputSchema=MemberKickInput.model_json_schema(),
        ),
        Tool(
            name="discord.member.ban",
            description="Ban a member from a Discord guild. Defaults to dry-run mode.",
            inputSchema=MemberBanInput.model_json_schema(),
        ),
        Tool(
            name="discord.member.timeout",
            description="Timeout a member in a Discord guild. Defaults to dry-run mode.",
            inputSchema=MemberTimeoutInput.model_json_schema(),
        ),
        Tool(
            name="discord.member.unban",
            description="Unban a member from a Discord guild. Defaults to dry-run mode.",
            inputSchema=MemberUnbanInput.model_json_schema(),
        ),
    ]


def get_handler(
    member_service: MemberService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.member.get":
            input_data = MemberGetInput.model_validate(arguments)
            result = await member_service.get_member(
                input_data.guild_id, input_data.user_id, scopes="member:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.member.get",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.member.list":
            input_data = MemberListInput.model_validate(arguments)
            result = await member_service.list_members(
                input_data.guild_id, scopes="member:read", limit=input_data.limit
            )
            await audit.record(
                workspace_id="system",
                action="discord.member.list",
                guild_id=input_data.guild_id,
                details={"limit": input_data.limit},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.member.kick":
            input_data = MemberKickInput.model_validate(arguments)
            result = await member_service.kick_member(
                input_data.guild_id,
                input_data.user_id,
                scopes="member:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.member.kick",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.member.ban":
            input_data = MemberBanInput.model_validate(arguments)
            result = await member_service.ban_member(
                input_data.guild_id,
                input_data.user_id,
                scopes="member:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
                delete_message_days=input_data.delete_message_days,
            )
            await audit.record(
                workspace_id="system",
                action="discord.member.ban",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
                details={
                    "dry_run": input_data.dry_run,
                    "delete_message_days": input_data.delete_message_days,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.member.timeout":
            input_data = MemberTimeoutInput.model_validate(arguments)
            result = await member_service.timeout_member(
                input_data.guild_id,
                input_data.user_id,
                input_data.duration_seconds,
                scopes="member:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.member.timeout",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
                details={
                    "dry_run": input_data.dry_run,
                    "duration_seconds": input_data.duration_seconds,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.member.unban":
            input_data = MemberUnbanInput.model_validate(arguments)
            result = await member_service.unban_member(
                input_data.guild_id,
                input_data.user_id,
                scopes="member:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.member.unban",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
