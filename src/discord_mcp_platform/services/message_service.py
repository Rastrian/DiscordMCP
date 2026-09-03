# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.models import (
    DiscordMessage,
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
        msg = await self._bot.get_message(channel_id, message_id)
        return {
            "id": msg.id,
            "channel_id": msg.channel_id,
            "author_id": msg.author_id,
            "author_name": msg.author_name,
            "content": msg.content,
            "timestamp": msg.timestamp,
        }

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

    async def send_embed(
        self,
        channel_id: str,
        content: str | None = None,
        embeds: list[dict] | None = None,
        scopes: str = "message:write",
    ) -> DiscordMessage:
        self._permissions.check_write(scopes, "message")
        if not self._permissions.check_channel_allowed(channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {channel_id} is not allowed")
        return await self._bot.send_rich_message(channel_id, content=content, embeds=embeds)

    # --- Reactions ---

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str, scopes: str) -> dict:
        self._permissions.check_write(scopes, "message")
        if not self._permissions.check_channel_allowed(channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {channel_id} is not allowed")
        await self._bot.add_reaction(channel_id, message_id, emoji)
        return {"status": "reacted", "emoji": emoji}

    async def remove_reaction(
        self, channel_id: str, message_id: str, emoji: str, scopes: str
    ) -> dict:
        self._permissions.check_write(scopes, "message")
        if not self._permissions.check_channel_allowed(channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {channel_id} is not allowed")
        await self._bot.remove_reaction(channel_id, message_id, emoji)
        return {"status": "removed", "emoji": emoji}

    async def list_reactions(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        scopes: str,
        limit: int = 25,
    ) -> list[dict]:
        self._permissions.check_read(scopes, "message")
        if not self._permissions.check_channel_allowed(channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {channel_id} is not allowed")
        return await self._bot.list_reactions(channel_id, message_id, emoji, limit=limit)

    async def remove_user_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        user_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "message")
        self._permissions.check_dangerous_operation("reaction.remove_user", dry_run, confirmation)
        if not self._permissions.check_channel_allowed(channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {channel_id} is not allowed")
        if dry_run:
            return {
                "status": "validated",
                "dry_run": True,
                "channel_id": channel_id,
                "message_id": message_id,
                "emoji": emoji,
                "user_id": user_id,
            }
        await self._bot.remove_user_reaction(channel_id, message_id, emoji, user_id)
        return {
            "status": "removed_user_reaction",
            "dry_run": False,
            "channel_id": channel_id,
            "message_id": message_id,
            "emoji": emoji,
            "user_id": user_id,
        }
