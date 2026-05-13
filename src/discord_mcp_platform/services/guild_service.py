# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.models import GuildListInput, GuildListOutput
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService

log = get_logger("guild_service")


class GuildService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def list_guilds(self, input_data: GuildListInput, scopes: str) -> GuildListOutput:
        self._permissions.check_read(scopes, "guild")
        guilds = await self._bot.list_guilds()
        return GuildListOutput(guilds=guilds)

    async def get_guild(self, guild_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "guild")
        guild = await self._bot.get_guild(guild_id)
        return {"guild_id": guild.id, "name": guild.name, "icon": guild.icon}

    async def modify_guild(
        self,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("guild.modify", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "guild.modify")
        if dry_run:
            return {"status": "validated", "dry_run": True, "guild_id": guild_id}
        guild = await self._bot.modify_guild(guild_id, **kwargs)
        return {"status": "updated", "dry_run": False, "guild_id": guild.id, "name": guild.name}
