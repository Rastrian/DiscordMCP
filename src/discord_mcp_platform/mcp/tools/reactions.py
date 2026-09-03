# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    ReactionAddInput,
    ReactionListInput,
    ReactionRemoveInput,
    ReactionRemoveUserInput,
)
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.message_service import MessageService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.reaction.add",
            description="Add a reaction to a Discord message.",
            inputSchema=ReactionAddInput.model_json_schema(),
        ),
        Tool(
            name="discord.reaction.remove",
            description="Remove the bot's reaction from a Discord message.",
            inputSchema=ReactionRemoveInput.model_json_schema(),
        ),
        Tool(
            name="discord.reaction.list",
            description="List users that reacted to a Discord message with a given emoji.",
            inputSchema=ReactionListInput.model_json_schema(),
        ),
        Tool(
            name="discord.reaction.remove_user",
            description=(
                "Remove another user's reaction from a Discord message. Defaults to dry-run mode."
            ),
            inputSchema=ReactionRemoveUserInput.model_json_schema(),
        ),
    ]


def get_handler(
    message_service: MessageService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.reaction.add":
            input_data = ReactionAddInput.model_validate(arguments)
            result = await message_service.add_reaction(
                input_data.channel_id,
                input_data.message_id,
                input_data.emoji,
                scopes="message:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.reaction.add",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={"emoji": input_data.emoji},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.reaction.remove":
            input_data = ReactionRemoveInput.model_validate(arguments)
            result = await message_service.remove_reaction(
                input_data.channel_id,
                input_data.message_id,
                input_data.emoji,
                scopes="message:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.reaction.remove",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={"emoji": input_data.emoji},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.reaction.list":
            input_data = ReactionListInput.model_validate(arguments)
            result = await message_service.list_reactions(
                input_data.channel_id,
                input_data.message_id,
                input_data.emoji,
                scopes="message:read",
                limit=input_data.limit,
            )
            await audit.record(
                workspace_id="system",
                action="discord.reaction.list",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={"emoji": input_data.emoji, "limit": input_data.limit},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.reaction.remove_user":
            input_data = ReactionRemoveUserInput.model_validate(arguments)
            result = await message_service.remove_user_reaction(
                input_data.channel_id,
                input_data.message_id,
                input_data.emoji,
                input_data.user_id,
                scopes="message:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.reaction.remove_user",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={
                    "dry_run": input_data.dry_run,
                    "emoji": input_data.emoji,
                    "user_id": input_data.user_id,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
