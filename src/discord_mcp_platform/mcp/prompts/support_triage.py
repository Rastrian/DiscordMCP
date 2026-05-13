# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from mcp.types import Prompt, PromptArgument


def get_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="support_triage",
            description="Triage support requests in a channel.",
            arguments=[
                PromptArgument(name="guild_id", description="Discord guild ID", required=True),
                PromptArgument(name="channel_id", description="Support channel ID", required=True),
            ],
        ),
    ]


async def handle(name: str, arguments: dict | None = None):
    if name != "support_triage":
        return None
    args = arguments or {}
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Review recent messages in support channel {args.get('channel_id', '')} "
                    f"in guild {args.get('guild_id', '')}. "
                    "Use discord.message.list_recent to read messages. "
                    "Categorize issues, identify urgent items, and suggest responses."
                ),
            },
        }
    ]
