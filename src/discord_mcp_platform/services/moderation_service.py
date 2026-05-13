# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService

log = get_logger("moderation_service")


class ModerationService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def delete_message(
        self,
        channel_id: str,
        message_id: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "message")
        self._permissions.check_dangerous_operation("message.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "message.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "message_id": message_id}
        await self._bot.delete_message(channel_id, message_id)
        return {"status": "deleted", "dry_run": False, "message_id": message_id}

    async def bulk_delete_messages(
        self,
        channel_id: str,
        message_ids: list[str],
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "message")
        self._permissions.check_dangerous_operation("message.bulk_delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "message.bulk_delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "count": len(message_ids)}
        await self._bot.bulk_delete_messages(channel_id, message_ids)
        return {"status": "deleted", "dry_run": False, "count": len(message_ids)}
