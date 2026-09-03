# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    EventListInput,
    EventGetInput,
    EventCreateInput,
    EventUpdateInput,
    EventDeleteInput,
    EventUsersInput,
)
from discord_mcp_platform.services.event_service import EventService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.event.list",
            description="List scheduled events in a Discord guild.",
            inputSchema=EventListInput.model_json_schema(),
        ),
        Tool(
            name="discord.event.get",
            description="Get a scheduled event of a Discord guild.",
            inputSchema=EventGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.event.create",
            description="Create a scheduled event in a Discord guild. Defaults to dry-run mode.",
            inputSchema=EventCreateInput.model_json_schema(),
        ),
        Tool(
            name="discord.event.update",
            description="Update a scheduled event in a Discord guild. Defaults to dry-run mode.",
            inputSchema=EventUpdateInput.model_json_schema(),
        ),
        Tool(
            name="discord.event.delete",
            description="Delete a scheduled event from a Discord guild. Defaults to dry-run mode.",
            inputSchema=EventDeleteInput.model_json_schema(),
        ),
        Tool(
            name="discord.event.list_users",
            description="List users interested in a scheduled event.",
            inputSchema=EventUsersInput.model_json_schema(),
        ),
    ]


def get_handler(
    event_service: EventService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.event.list":
            input_data = EventListInput.model_validate(arguments)
            result = await event_service.list_events(input_data.guild_id, scopes="guild:read")
            await audit.record(
                workspace_id="system",
                action="discord.event.list",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.event.get":
            input_data = EventGetInput.model_validate(arguments)
            result = await event_service.get_event(
                input_data.guild_id, input_data.event_id, scopes="guild:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.event.get",
                guild_id=input_data.guild_id,
                target_id=input_data.event_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.event.create":
            input_data = EventCreateInput.model_validate(arguments)
            result = await event_service.create_event(
                input_data.guild_id,
                input_data.name,
                input_data.scheduled_start_time,
                scopes="guild:write",
                description=input_data.description,
                entity_type=input_data.entity_type,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.event.create",
                guild_id=input_data.guild_id,
                details={"dry_run": input_data.dry_run, "name": input_data.name},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.event.update":
            input_data = EventUpdateInput.model_validate(arguments)
            updates = input_data.model_dump(
                exclude_unset=True, exclude={"guild_id", "event_id", "dry_run", "confirmation"}
            )
            result = await event_service.update_event(
                input_data.guild_id,
                input_data.event_id,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
                **updates,
            )
            await audit.record(
                workspace_id="system",
                action="discord.event.update",
                guild_id=input_data.guild_id,
                target_id=input_data.event_id,
                details={"dry_run": input_data.dry_run, "fields": sorted(updates)},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.event.delete":
            input_data = EventDeleteInput.model_validate(arguments)
            result = await event_service.delete_event(
                input_data.guild_id,
                input_data.event_id,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.event.delete",
                guild_id=input_data.guild_id,
                target_id=input_data.event_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.event.list_users":
            input_data = EventUsersInput.model_validate(arguments)
            result = await event_service.list_event_users(
                input_data.guild_id,
                input_data.event_id,
                scopes="guild:read",
                limit=input_data.limit,
            )
            await audit.record(
                workspace_id="system",
                action="discord.event.list_users",
                guild_id=input_data.guild_id,
                target_id=input_data.event_id,
                details={"limit": input_data.limit},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
