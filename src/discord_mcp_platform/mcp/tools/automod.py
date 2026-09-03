# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    AutomodListInput,
    AutomodGetInput,
    AutomodCreateInput,
    AutomodUpdateInput,
    AutomodDeleteInput,
)
from discord_mcp_platform.services.automod_service import AutomodService
from discord_mcp_platform.services.audit_service import AuditService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.automod.list",
            description="List auto-moderation rules of a Discord guild.",
            inputSchema=AutomodListInput.model_json_schema(),
        ),
        Tool(
            name="discord.automod.get",
            description="Get an auto-moderation rule of a Discord guild.",
            inputSchema=AutomodGetInput.model_json_schema(),
        ),
        Tool(
            name="discord.automod.create",
            description=(
                "Create an auto-moderation rule in a Discord guild. Defaults to dry-run mode."
            ),
            inputSchema=AutomodCreateInput.model_json_schema(),
        ),
        Tool(
            name="discord.automod.update",
            description=(
                "Update an auto-moderation rule in a Discord guild. Defaults to dry-run mode."
            ),
            inputSchema=AutomodUpdateInput.model_json_schema(),
        ),
        Tool(
            name="discord.automod.delete",
            description=(
                "Delete an auto-moderation rule from a Discord guild. Defaults to dry-run mode."
            ),
            inputSchema=AutomodDeleteInput.model_json_schema(),
        ),
    ]


def get_handler(
    automod_service: AutomodService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.automod.list":
            input_data = AutomodListInput.model_validate(arguments)
            result = await automod_service.list_rules(input_data.guild_id, scopes="guild:read")
            await audit.record(
                workspace_id="system",
                action="discord.automod.list",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.automod.get":
            input_data = AutomodGetInput.model_validate(arguments)
            result = await automod_service.get_rule(
                input_data.guild_id, input_data.rule_id, scopes="guild:read"
            )
            await audit.record(
                workspace_id="system",
                action="discord.automod.get",
                guild_id=input_data.guild_id,
                target_id=input_data.rule_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.automod.create":
            input_data = AutomodCreateInput.model_validate(arguments)
            result = await automod_service.create_rule(
                input_data.guild_id,
                input_data.name,
                input_data.event_type,
                input_data.trigger,
                input_data.actions,
                scopes="guild:write",
                enabled=input_data.enabled,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.automod.create",
                guild_id=input_data.guild_id,
                details={"dry_run": input_data.dry_run, "name": input_data.name},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.automod.update":
            input_data = AutomodUpdateInput.model_validate(arguments)
            updates = input_data.model_dump(
                exclude_unset=True, exclude={"guild_id", "rule_id", "dry_run", "confirmation"}
            )
            result = await automod_service.update_rule(
                input_data.guild_id,
                input_data.rule_id,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
                **updates,
            )
            await audit.record(
                workspace_id="system",
                action="discord.automod.update",
                guild_id=input_data.guild_id,
                target_id=input_data.rule_id,
                details={"dry_run": input_data.dry_run, "fields": sorted(updates)},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.automod.delete":
            input_data = AutomodDeleteInput.model_validate(arguments)
            result = await automod_service.delete_rule(
                input_data.guild_id,
                input_data.rule_id,
                scopes="guild:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.automod.delete",
                guild_id=input_data.guild_id,
                target_id=input_data.rule_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
