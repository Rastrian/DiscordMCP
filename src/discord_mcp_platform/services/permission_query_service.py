# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService


class PermissionQueryService:
    """Read-only access to Discord's computed-permission endpoints."""

    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def get_guild_member_permissions(self, guild_id: str, user_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "permissions.read")
        return await self._bot.get_guild_member_permissions(guild_id, user_id)

    async def get_guild_role_permissions(self, guild_id: str, role_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "permissions.read")
        return await self._bot.get_guild_role_permissions(guild_id, role_id)

    async def get_channel_member_permissions(
        self, channel_id: str, user_id: str, scopes: str
    ) -> dict:
        self._permissions.check_read(scopes, "channel")
        guild_id = await self._channel_guild_id(channel_id)
        await check_discord_permission(self._bot, guild_id, "permissions.channel_read")
        return await self._bot.get_channel_member_permissions(channel_id, user_id)

    async def get_channel_role_permissions(
        self, channel_id: str, role_id: str, scopes: str
    ) -> dict:
        self._permissions.check_read(scopes, "channel")
        guild_id = await self._channel_guild_id(channel_id)
        await check_discord_permission(self._bot, guild_id, "permissions.channel_read")
        return await self._bot.get_channel_role_permissions(channel_id, role_id)

    async def _channel_guild_id(self, channel_id: str) -> str:
        """Resolve the guild that owns *channel_id* for the bot permission gate."""
        channel = await self._bot.get_channel(channel_id)
        return channel.guild_id
