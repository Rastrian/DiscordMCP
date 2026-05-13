# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from mcp.types import Prompt, PromptArgument


def get_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="moderation_review",
            description="Review recent messages for moderation concerns.",
            arguments=[
                PromptArgument(name="guild_id", description="Discord guild ID", required=True),
                PromptArgument(
                    name="channel_id", description="Channel ID to review", required=True
                ),
            ],
        ),
    ]


async def handle(name: str, arguments: dict | None = None):
    if name != "moderation_review":
        return None
    args = arguments or {}
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Review recent messages in guild {args.get('guild_id', '')} "
                    f"channel {args.get('channel_id', '')} for moderation concerns. "
                    "Look for rule violations, spam, harassment, or inappropriate content. "
                    "Use discord.message.list_recent to fetch messages. "
                    "Draft a moderation warning if needed."
                ),
            },
        }
    ]
