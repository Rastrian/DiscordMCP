# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    RoleListInput,
    RoleCreateInput,
    RoleModifyInput,
    RoleDeleteInput,
    RoleAssignInput,
    RoleRemoveInput,
)
from discord_mcp_platform.services.role_service import RoleService
from discord_mcp_platform.services.audit_service import AuditService

SNOWFLAKE = {"type": "string", "pattern": "^[0-9]{15,25}$"}


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.role.list",
            description="List roles in a Discord guild.",
            inputSchema=RoleListInput.model_json_schema(),
        ),
        Tool(
            name="discord.role.create",
            description="Create a new role in a Discord guild. Defaults to dry-run mode.",
            inputSchema=RoleCreateInput.model_json_schema(),
        ),
        Tool(
            name="discord.role.modify",
            description="Modify an existing role in a Discord guild. Defaults to dry-run mode.",
            inputSchema=RoleModifyInput.model_json_schema(),
        ),
        Tool(
            name="discord.role.delete",
            description="Delete a role from a Discord guild. Defaults to dry-run mode.",
            inputSchema=RoleDeleteInput.model_json_schema(),
        ),
        Tool(
            name="discord.role.reorder",
            description="Reorder roles in a Discord guild.",
            inputSchema={
                "type": "object",
                "properties": {
                    "guild_id": SNOWFLAKE,
                    "positions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": SNOWFLAKE,
                                "position": {"type": "integer", "minimum": 0},
                            },
                            "required": ["id", "position"],
                        },
                        "minItems": 1,
                    },
                },
                "required": ["guild_id", "positions"],
            },
        ),
        Tool(
            name="discord.role.assign",
            description="Assign a role to a member in a Discord guild. Defaults to dry-run mode.",
            inputSchema=RoleAssignInput.model_json_schema(),
        ),
        Tool(
            name="discord.role.remove",
            description="Remove a role from a member in a Discord guild. Defaults to dry-run mode.",
            inputSchema=RoleRemoveInput.model_json_schema(),
        ),
    ]


def get_handler(
    role_service: RoleService, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.role.list":
            input_data = RoleListInput.model_validate(arguments)
            result = await role_service.list_roles(input_data.guild_id, scopes="role:read")
            await audit.record(
                workspace_id="system",
                action="discord.role.list",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.role.create":
            input_data = RoleCreateInput.model_validate(arguments)
            result = await role_service.create_role(
                input_data.guild_id,
                input_data.name,
                scopes="role:write",
                color=input_data.color,
                hoist=input_data.hoist,
                permissions=input_data.permissions,
                mentionable=input_data.mentionable,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.role.create",
                guild_id=input_data.guild_id,
                details={"dry_run": input_data.dry_run, "name": input_data.name},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.role.modify":
            input_data = RoleModifyInput.model_validate(arguments)
            result = await role_service.modify_role(
                input_data.guild_id,
                input_data.role_id,
                scopes="role:write",
                name=input_data.name,
                color=input_data.color,
                hoist=input_data.hoist,
                permissions=input_data.permissions,
                mentionable=input_data.mentionable,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.role.modify",
                guild_id=input_data.guild_id,
                target_id=input_data.role_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.role.delete":
            input_data = RoleDeleteInput.model_validate(arguments)
            result = await role_service.delete_role(
                input_data.guild_id,
                input_data.role_id,
                scopes="role:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.role.delete",
                guild_id=input_data.guild_id,
                target_id=input_data.role_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.role.reorder":
            guild_id = arguments["guild_id"]
            positions = arguments["positions"]
            result = await role_service.reorder_roles(guild_id, positions, scopes="role:write")
            await audit.record(
                workspace_id="system",
                action="discord.role.reorder",
                guild_id=guild_id,
                details={"count": len(positions)},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.role.assign":
            input_data = RoleAssignInput.model_validate(arguments)
            result = await role_service.add_role(
                input_data.guild_id,
                input_data.user_id,
                input_data.role_id,
                scopes="role:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.role.assign",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
                details={
                    "dry_run": input_data.dry_run,
                    "role_id": input_data.role_id,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.role.remove":
            input_data = RoleRemoveInput.model_validate(arguments)
            result = await role_service.remove_role(
                input_data.guild_id,
                input_data.user_id,
                input_data.role_id,
                scopes="role:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.role.remove",
                guild_id=input_data.guild_id,
                target_id=input_data.user_id,
                details={
                    "dry_run": input_data.dry_run,
                    "role_id": input_data.role_id,
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
