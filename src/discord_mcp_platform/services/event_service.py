# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService


class EventService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def list_events(self, guild_id: str, scopes: str) -> list[dict]:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "event.read")
        return await self._bot.list_scheduled_events(guild_id)

    async def get_event(self, guild_id: str, event_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "event.read")
        return await self._bot.get_scheduled_event(guild_id, event_id)

    async def list_event_users(
        self, guild_id: str, event_id: str, scopes: str, limit: int = 100
    ) -> list[dict]:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "event.read")
        return await self._bot.list_scheduled_event_users(guild_id, event_id, limit=limit)

    async def create_event(
        self,
        guild_id: str,
        name: str,
        scheduled_start_time: str,
        scopes: str,
        description: str | None = None,
        entity_type: int | None = None,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("event.create", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "event.create")
        if dry_run:
            return {"status": "validated", "dry_run": True, "name": name}
        body: dict = {
            "name": name,
            "scheduled_start_time": scheduled_start_time,
            "privacy_level": 2,
        }
        if description is not None:
            body["description"] = description
        if entity_type is not None:
            body["entity_type"] = entity_type
        event = await self._bot.create_scheduled_event(guild_id, **body)
        return {
            "status": "created",
            "dry_run": False,
            "event_id": event["id"],
            "name": event.get("name", name),
        }

    async def update_event(
        self,
        guild_id: str,
        event_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("event.update", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "event.update")
        if dry_run:
            return {"status": "validated", "dry_run": True, "event_id": event_id}
        event = await self._bot.update_scheduled_event(guild_id, event_id, **kwargs)
        return {"status": "updated", "dry_run": False, "event_id": event["id"]}

    async def delete_event(
        self,
        guild_id: str,
        event_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("event.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "event.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "event_id": event_id}
        await self._bot.delete_scheduled_event(guild_id, event_id)
        return {"status": "deleted", "dry_run": False, "event_id": event_id}
