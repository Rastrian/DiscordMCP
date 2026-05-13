# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService

log = get_logger("webhook_service")


class WebhookService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def create_webhook(
        self,
        channel_id: str,
        name: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("webhook.create", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "webhook.create")
        if dry_run:
            return {"status": "validated", "dry_run": True, "name": name}
        data = await self._bot.create_webhook(channel_id, name)
        return {
            "status": "created",
            "dry_run": False,
            "webhook_id": data["id"],
            "name": data.get("name", name),
        }

    async def list_webhooks(self, guild_id: str, scopes: str) -> list[dict]:
        self._permissions.check_read(scopes, "channel")
        await check_discord_permission(self._bot, guild_id, "webhook.list")
        data = await self._bot.list_webhooks(guild_id)
        return [
            {
                "webhook_id": w["id"],
                "name": w.get("name", ""),
                "channel_id": w.get("channel_id", ""),
            }
            for w in data
        ]

    async def get_webhook(self, webhook_id: str, guild_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "channel")
        await check_discord_permission(self._bot, guild_id, "webhook.list")
        webhook = await self._bot.get_webhook(webhook_id)
        return {"webhook_id": webhook.id, "name": webhook.name, "channel_id": webhook.channel_id}

    async def modify_webhook(
        self,
        webhook_id: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("webhook.modify", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "webhook.modify")
        if dry_run:
            return {"status": "validated", "dry_run": True, "webhook_id": webhook_id}
        webhook = await self._bot.modify_webhook(webhook_id, **kwargs)
        return {
            "status": "updated",
            "dry_run": False,
            "webhook_id": webhook.id,
            "name": webhook.name,
        }

    async def delete_webhook(
        self,
        webhook_id: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("webhook.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "webhook.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "webhook_id": webhook_id}
        await self._bot.delete_webhook(webhook_id)
        return {"status": "deleted", "dry_run": False, "webhook_id": webhook_id}

    async def execute_webhook(
        self,
        webhook_id: str,
        webhook_token: str,
        guild_id: str,
        content: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("webhook.execute", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "webhook.execute")
        if dry_run:
            return {"status": "validated", "dry_run": True, "webhook_id": webhook_id}
        data = await self._bot.execute_webhook(webhook_id, webhook_token, content=content, **kwargs)
        return {"status": "sent", "dry_run": False, "message_id": data.get("id", "")}
