# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    MessageDeleteInput,
    MessageBulkDeleteInput,
)
from discord_mcp_platform.services.moderation_service import ModerationService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.message.delete",
            description="Delete a single message from a Discord channel. Defaults to dry-run mode.",
            inputSchema=MessageDeleteInput.model_json_schema(),
        ),
        Tool(
            name="discord.message.bulk_delete",
            description="Bulk delete messages from a Discord channel. Defaults to dry-run mode.",
            inputSchema=MessageBulkDeleteInput.model_json_schema(),
        ),
    ]


def get_handler(
    moderation_service: ModerationService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.message.delete":
            input_data = MessageDeleteInput.model_validate(arguments)
            result = await moderation_service.delete_message(
                input_data.channel_id,
                input_data.message_id,
                input_data.guild_id,
                scopes="moderation:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.message.delete",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.message.bulk_delete":
            input_data = MessageBulkDeleteInput.model_validate(arguments)
            result = await moderation_service.bulk_delete_messages(
                input_data.channel_id,
                input_data.message_ids,
                input_data.guild_id,
                scopes="moderation:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.message.bulk_delete",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                details={
                    "dry_run": input_data.dry_run,
                    "count": len(input_data.message_ids),
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
