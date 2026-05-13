# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from collections.abc import Callable, Awaitable

from mcp.types import Tool, TextContent

from discord_mcp_platform.discord.models import (
    WebhookCreateInput,
    WebhookListInput,
    WebhookModifyInput,
    WebhookDeleteInput,
    WebhookExecuteInput,
)
from discord_mcp_platform.services.audit_service import AuditService

SNOWFLAKE = {"type": "string", "pattern": "^[0-9]{15,25}$"}


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="discord.webhook.create",
            description="Create a webhook in a Discord channel. Defaults to dry-run mode.",
            inputSchema=WebhookCreateInput.model_json_schema(),
        ),
        Tool(
            name="discord.webhook.list",
            description="List webhooks in a Discord guild.",
            inputSchema=WebhookListInput.model_json_schema(),
        ),
        Tool(
            name="discord.webhook.get",
            description="Get a webhook by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "guild_id": SNOWFLAKE,
                    "webhook_id": SNOWFLAKE,
                },
                "required": ["guild_id", "webhook_id"],
            },
        ),
        Tool(
            name="discord.webhook.modify",
            description="Modify a webhook. Defaults to dry-run mode.",
            inputSchema=WebhookModifyInput.model_json_schema(),
        ),
        Tool(
            name="discord.webhook.delete",
            description="Delete a webhook. Defaults to dry-run mode.",
            inputSchema=WebhookDeleteInput.model_json_schema(),
        ),
        Tool(
            name="discord.webhook.execute",
            description="Execute a webhook to send a message. Defaults to dry-run mode.",
            inputSchema=WebhookExecuteInput.model_json_schema(),
        ),
    ]


def get_handler(
    webhook_service, audit: AuditService
) -> Callable[[str, dict], Awaitable[list[TextContent] | None]]:
    async def handle(name: str, arguments: dict) -> list[TextContent] | None:
        if name == "discord.webhook.create":
            input_data = WebhookCreateInput.model_validate(arguments)
            result = await webhook_service.create_webhook(
                input_data.guild_id,
                input_data.channel_id,
                input_data.name,
                scopes="channel:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.webhook.create",
                guild_id=input_data.guild_id,
                channel_id=input_data.channel_id,
                details={"dry_run": input_data.dry_run, "name": input_data.name},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.webhook.list":
            input_data = WebhookListInput.model_validate(arguments)
            result = await webhook_service.list_webhooks(input_data.guild_id, scopes="channel:read")
            await audit.record(
                workspace_id="system",
                action="discord.webhook.list",
                guild_id=input_data.guild_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.webhook.get":
            guild_id = arguments["guild_id"]
            webhook_id = arguments["webhook_id"]
            result = await webhook_service.get_webhook(guild_id, webhook_id, scopes="channel:read")
            await audit.record(
                workspace_id="system",
                action="discord.webhook.get",
                guild_id=guild_id,
                target_id=webhook_id,
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.webhook.modify":
            input_data = WebhookModifyInput.model_validate(arguments)
            result = await webhook_service.modify_webhook(
                input_data.guild_id,
                input_data.webhook_id,
                scopes="channel:write",
                name=input_data.name,
                channel_id=input_data.channel_id,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.webhook.modify",
                guild_id=input_data.guild_id,
                target_id=input_data.webhook_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.webhook.delete":
            input_data = WebhookDeleteInput.model_validate(arguments)
            result = await webhook_service.delete_webhook(
                input_data.guild_id,
                input_data.webhook_id,
                scopes="channel:write",
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.webhook.delete",
                guild_id=input_data.guild_id,
                target_id=input_data.webhook_id,
                details={"dry_run": input_data.dry_run},
            )
            return [TextContent(type="text", text=json.dumps(result))]

        if name == "discord.webhook.execute":
            input_data = WebhookExecuteInput.model_validate(arguments)
            result = await webhook_service.execute_webhook(
                input_data.guild_id,
                input_data.webhook_id,
                input_data.webhook_token,
                input_data.content,
                scopes="message:write",
                username=input_data.username,
                dry_run=input_data.dry_run,
                confirmation=input_data.confirmation,
            )
            await audit.record(
                workspace_id="system",
                action="discord.webhook.execute",
                guild_id=input_data.guild_id,
                target_id=input_data.webhook_id,
                details={
                    "dry_run": input_data.dry_run,
                    "content_length": len(input_data.content),
                },
            )
            return [TextContent(type="text", text=json.dumps(result))]

        return None

    return handle
