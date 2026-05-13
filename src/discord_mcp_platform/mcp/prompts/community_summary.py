# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from mcp.types import Prompt, PromptArgument


def get_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="community_summary",
            description="Summarize community activity in a Discord guild.",
            arguments=[
                PromptArgument(name="guild_id", description="Discord guild ID", required=True),
            ],
        ),
    ]


async def handle(name: str, arguments: dict | None = None):
    if name != "community_summary":
        return None
    guild_id = (arguments or {}).get("guild_id", "")
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Summarize the recent community activity in guild {guild_id}. "
                    "Use discord.channel.list to find channels, then discord.message.list_recent "
                    "to read recent messages. Provide a concise summary of discussion topics, "
                    "active members, and any notable events."
                ),
            },
        }
    ]
