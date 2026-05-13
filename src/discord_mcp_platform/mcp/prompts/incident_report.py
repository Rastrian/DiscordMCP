# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from mcp.types import Prompt, PromptArgument


def get_prompts() -> list[Prompt]:
    return [
        Prompt(
            name="incident_report",
            description="Create an incident thread and draft an incident report.",
            arguments=[
                PromptArgument(name="guild_id", description="Discord guild ID", required=True),
                PromptArgument(
                    name="channel_id", description="Channel for the incident thread", required=True
                ),
                PromptArgument(
                    name="description", description="Incident description", required=True
                ),
            ],
        ),
    ]


async def handle(name: str, arguments: dict | None = None):
    if name != "incident_report":
        return None
    args = arguments or {}
    return [
        {
            "role": "user",
            "content": {
                "type": "text",
                "text": (
                    f"Create a private incident thread in guild {args.get('guild_id', '')} "
                    f"channel {args.get('channel_id', '')}. "
                    f"Incident: {args.get('description', '')}. "
                    "Use discord.thread.create with private=true, then post an incident summary."
                ),
            },
        }
    ]
