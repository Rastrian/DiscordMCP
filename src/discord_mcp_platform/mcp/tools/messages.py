# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    MessageListRecentInput,
    MessageSendInput,
    MessageGetInput,
    MessageEditInput,
)
from discord_mcp_platform.services.message_service import MessageService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.message.list_recent",
            description="List recent messages from a Discord channel.",
            inputSchema=MessageListRecentInput.model_json_schema(),
        ),
        Tool(
            name="discord.message.send",
            description="Send a message to a Discord channel. Defaults to dry-run mode.",
            inputSchema=MessageSendInput.model_json_schema(),
        ),
        Tool(
            name="discord.message.get",
            description="Get a single message from a Discord channel.",
            inputSchema=MessageGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.message.edit",
            description="Edit a message in a Discord channel. Defaults to dry-run mode.",
            inputSchema=MessageEditInput.model_json_schema(),
        ),
    ]


def get_handler(
    message_service: MessageService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.message.list_recent":
            input_data = MessageListRecentInput.model_validate(arguments)
            result = await message_service.list_recent(input_data, scopes="message:read")
            await audit.record(
                workspace_id="system",
                action="discord.message.list_recent",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        if name == "discord.message.send":
            input_data = MessageSendInput.model_validate(arguments)
            result = await message_service.send(input_data, scopes="message:write")
            await audit.record(
                workspace_id="system",
                action="discord.message.send",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                details={
                    "dry_run": input_data.dry_run,
                    "content_length": len(input_data.content),
                },
            )
            return [TextContent(type="text", text=result.model_dump_json())]

        if name == "discord.message.get":
            input_data = MessageGetInput.model_validate(arguments)
            result = await message_service.get_message(
                input_data.channel_id,
                input_data.message_id,
                scopes="message:read",
            )
            await audit.record(
                workspace_id="system",
                action="discord.message.get",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.message.edit":
            input_data = MessageEditInput.model_validate(arguments)
            result = await message_service.edit_message(
                input_data.channel_id,
                input_data.message_id,
                input_data.content,
                input_data.guild_id,
                scopes="message:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.message.edit",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={
                    "dry_run": input_data.dry_run,
                    "content_length": len(input_data.content),
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
