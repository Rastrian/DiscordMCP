# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from mcp.types import Prompt, PromptArgument


def get_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="automation_builder",
            description="Build an automation for a Discord guild from a description.",
            arguments=[
                PromptArgument(name="guild_id", description="Discord guild ID", required=True),
                PromptArgument(
                    name="description", description="What the automation should do", required=True
                ),
            ],
        ),
    ]


async def handle(name: str, arguments: dict | None = None):
    if name != "automation_builder":
        return None
    args = arguments or {}
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Create an automation for guild {args.get('guild_id', '')}. "
                    f"Description: {args.get('description', '')}. "
                    "Use discord.automation.draft to create a draft automation. "
                    "The automation should be safe and follow community guidelines."
                ),
            },
        }
    ]
