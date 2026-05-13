# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.models import (
    MessageListRecentInput,
    MessageListRecentOutput,
    MessageSendInput,
    MessageSendOutput,
)
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.security.validation import validate_message_content

log = get_logger("message_service")


class MessageService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def list_recent(
        self, input_data: MessageListRecentInput, scopes: str
    ) -> MessageListRecentOutput:
        self._permissions.check_read(scopes, "message")
        if not self._permissions.check_channel_allowed(input_data.channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {input_data.channel_id} is not allowed")
        messages = await self._bot.list_recent_messages(input_data.channel_id, input_data.limit)
        return MessageListRecentOutput(channel_id=input_data.channel_id, messages=messages)

    async def send(self, input_data: MessageSendInput, scopes: str) -> MessageSendOutput:
        self._permissions.check_write(scopes, "message")
        self._permissions.check_dangerous_operation(
            "message.send", input_data.dry_run, input_data.confirmation
        )
        if not self._permissions.check_channel_allowed(input_data.channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {input_data.channel_id} is not allowed")

        validate_message_content(input_data.content)

        if input_data.dry_run:
            log.info("message_send_dry_run", channel_id=input_data.channel_id)
            return MessageSendOutput(status="validated", dry_run=True, message_id=None)

        msg = await self._bot.send_message(input_data.channel_id, input_data.content)
        log.info("message_sent", channel_id=input_data.channel_id, message_id=msg.id)
        return MessageSendOutput(status="sent", dry_run=False, message_id=msg.id)

    async def get_message(self, channel_id: str, message_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "message")
        return {"channel_id": channel_id, "message_id": message_id}

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "message")
        self._permissions.check_dangerous_operation("message.edit", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "message.edit")
        if dry_run:
            return {"status": "validated", "dry_run": True, "message_id": message_id}
        msg = await self._bot.edit_message(channel_id, message_id, content)
        return {
            "status": "edited",
            "dry_run": False,
            "message_id": msg.id,
            "content_length": len(msg.content),
        }
