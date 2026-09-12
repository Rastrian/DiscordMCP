# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    InviteCreateInput,
    InviteListInput,
    InviteGetInput,
    InviteDeleteInput,
    InviteTargetAddInput,
    InviteTargetRemoveInput,
    InviteTargetBulkAddInput,
    InviteTargetBulkRemoveInput,
)
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.invite.create",
            description="Create an invite for a Discord channel. Defaults to dry-run mode.",
            inputSchema=InviteCreateInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.list",
            description="List invites for a Discord guild.",
            inputSchema=InviteListInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.get",
            description="Get an invite by code.",
            inputSchema=InviteGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.delete",
            description="Delete (revoke) an invite. Defaults to dry-run mode.",
            inputSchema=InviteDeleteInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.target.add",
            description="Add a target user to an existing invite. Defaults to dry-run mode.",
            inputSchema=InviteTargetAddInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.target.remove",
            description="Remove a target user from an existing invite. Defaults to dry-run mode.",
            inputSchema=InviteTargetRemoveInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.target.bulk_add",
            description="Bulk add target users to an existing invite. Defaults to dry-run mode.",
            inputSchema=InviteTargetBulkAddInput.model_json_schema(),
        ),
        Tool(
            name="discord.invite.target.bulk_remove",
            description=(
                "Bulk remove target users from an existing invite. Defaults to dry-run mode."
            ),
            inputSchema=InviteTargetBulkRemoveInput.model_json_schema(),
        ),
    ]


def get_handler(
    invite_service, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.invite.create":
            input_data = InviteCreateInput.model_validate(arguments)
            result = await invite_service.create_invite(
                channel_id=input_data.channel_id,
                guild_id=input_data.guild_id,
                scopes="channel:write",
                max_age=input_data.max_age,
                max_uses=input_data.max_uses,
                temporary=input_data.temporary,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.invite.create",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                details={
                    "dry_run": input_data.dry_run,
                    "max_age": input_data.max_age,
                    "max_uses": input_data.max_uses,
                    "temporary": input_data.temporary,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.list":
            input_data = InviteListInput.model_validate(arguments)
            result = await invite_service.list_invites(input_data.guild_id, scopes="channel:read")
            await audit.record(
                workspace_id="system",
                action="discord.invite.list",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.get":
            input_data = InviteGetInput.model_validate(arguments)
            result = await invite_service.get_invite(input_data.code, scopes="channel:read")
            await audit.record(
                workspace_id="system",
                action="discord.invite.get",
                target_id=input_data.code,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.delete":
            input_data = InviteDeleteInput.model_validate(arguments)
            result = await invite_service.delete_invite(
                code=input_data.code,
                guild_id=input_data.guild_id,
                scopes="channel:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.invite.delete",
                guild_id=input_data.guild_id,
                target_id=input_data.code,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.target.add":
            input_data = InviteTargetAddInput.model_validate(arguments)
            result = await invite_service.add_invite_target_user(
                code=input_data.code,
                guild_id=input_data.guild_id,
                user_id=input_data.user_id,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.invite.target.add",
                guild_id=input_data.guild_id,
                target_id=input_data.code,
                details={"dry_run": input_data.dry_run, "user_id": input_data.user_id},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.target.remove":
            input_data = InviteTargetRemoveInput.model_validate(arguments)
            result = await invite_service.remove_invite_target_user(
                code=input_data.code,
                guild_id=input_data.guild_id,
                user_id=input_data.user_id,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.invite.target.remove",
                guild_id=input_data.guild_id,
                target_id=input_data.code,
                details={"dry_run": input_data.dry_run, "user_id": input_data.user_id},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.target.bulk_add":
            input_data = InviteTargetBulkAddInput.model_validate(arguments)
            result = await invite_service.bulk_add_invite_target_users(
                code=input_data.code,
                guild_id=input_data.guild_id,
                user_ids=input_data.user_ids,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.invite.target.bulk_add",
                guild_id=input_data.guild_id,
                target_id=input_data.code,
                details={"dry_run": input_data.dry_run, "user_ids": input_data.user_ids},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.invite.target.bulk_remove":
            input_data = InviteTargetBulkRemoveInput.model_validate(arguments)
            result = await invite_service.bulk_remove_invite_target_users(
                code=input_data.code,
                guild_id=input_data.guild_id,
                user_ids=input_data.user_ids,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.invite.target.bulk_remove",
                guild_id=input_data.guild_id,
                target_id=input_data.code,
                details={"dry_run": input_data.dry_run, "user_ids": input_data.user_ids},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
