# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Awaitable, Callable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import ReactionAddInput, ReactionRemoveInput
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.services.audit_service import AuditService


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
    ]


def get_handler(
    bot: BotRuntime, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.reaction.add":
            input_data = ReactionAddInput.model_validate(arguments)
            await bot.add_reaction(input_data.channel_id, input_data.message_id, input_data.emoji)
            await audit.record(
                workspace_id="system",
                action="discord.reaction.add",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={"emoji": input_data.emoji},
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"status": "reacted", "emoji": input_data.emoji}),
                )
            ]

        if name == "discord.reaction.remove":
            input_data = ReactionRemoveInput.model_validate(arguments)
            await bot.remove_reaction(
                input_data.channel_id, input_data.message_id, input_data.emoji
            )
            await audit.record(
                workspace_id="system",
                action="discord.reaction.remove",
                channel_id=input_data.channel_id,
                target_id=input_data.message_id,
                details={"emoji": input_data.emoji},
            )
            return [
                TextContent(
                    type="text",
                    text=json.dumps({"status": "removed", "emoji": input_data.emoji}),
                )
            ]

        return None

    return handle
