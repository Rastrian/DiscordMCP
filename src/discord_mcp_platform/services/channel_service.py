# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.models import ChannelListInput, ChannelListOutput
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService

log = get_logger("channel_service")


class ChannelService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def list_channels(self, input_data: ChannelListInput, scopes: str) -> ChannelListOutput:
        self._permissions.check_read(scopes, "channel")
        if not self._permissions.check_guild_allowed(input_data.guild_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"guild {input_data.guild_id} is not allowed")
        await check_discord_permission(self._bot, input_data.guild_id, "channel.read")
        channels = await self._bot.list_channels(input_data.guild_id)
        return ChannelListOutput(guild_id=input_data.guild_id, channels=channels)

    async def create_channel(
        self,
        guild_id: str,
        name: str,
        scopes: str,
        channel_type: int = 0,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("channel.create", dry_run, confirmation)
        if not self._permissions.check_guild_allowed(guild_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"guild {guild_id} is not allowed")
        await check_discord_permission(self._bot, guild_id, "channel.create")
        if dry_run:
            return {"status": "validated", "dry_run": True, "name": name}
        channel = await self._bot.create_channel(guild_id, name, channel_type, **kwargs)
        return {
            "status": "created",
            "dry_run": False,
            "channel_id": channel.id,
            "name": channel.name,
            "parent_id": channel.parent_id,
        }

    async def delete_channel(
        self,
        channel_id: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("channel.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "channel.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "channel_id": channel_id}
        await self._bot.delete_channel(channel_id)
        return {"status": "deleted", "dry_run": False, "channel_id": channel_id}

    async def get_channel(self, channel_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "channel")
        await check_discord_permission(
            self._bot, "", "channel.read"
        )  # no guild check for single channel
        channel = await self._bot.get_channel(channel_id)
        return {"channel_id": channel.id, "name": channel.name, "type": channel.type}

    async def edit_channel(
        self,
        channel_id: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("channel.edit", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "channel.modify")
        if dry_run:
            return {"status": "validated", "dry_run": True, "channel_id": channel_id}
        channel = await self._bot.modify_channel(channel_id, **kwargs)
        return {
            "status": "updated",
            "dry_run": False,
            "channel_id": channel.id,
            "name": channel.name,
        }

    async def edit_permissions(
        self,
        channel_id: str,
        guild_id: str,
        overwrite_id: str,
        allow: str,
        deny: str,
        overwrite_type: int,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation(
            "channel.permission_change", dry_run, confirmation
        )
        await check_discord_permission(self._bot, guild_id, "channel.permission_overwrite")
        if dry_run:
            return {
                "status": "validated",
                "dry_run": True,
                "channel_id": channel_id,
                "overwrite_id": overwrite_id,
            }
        await self._bot.edit_channel_permissions(
            channel_id, overwrite_id, allow, deny, overwrite_type
        )
        return {
            "status": "updated",
            "dry_run": False,
            "channel_id": channel_id,
            "overwrite_id": overwrite_id,
        }

    async def delete_permissions(
        self,
        channel_id: str,
        guild_id: str,
        overwrite_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation(
            "channel.permission_change", dry_run, confirmation
        )
        await check_discord_permission(self._bot, guild_id, "channel.permission_overwrite")
        if dry_run:
            return {
                "status": "validated",
                "dry_run": True,
                "channel_id": channel_id,
                "overwrite_id": overwrite_id,
            }
        await self._bot.delete_channel_permissions(channel_id, overwrite_id)
        return {
            "status": "deleted",
            "dry_run": False,
            "channel_id": channel_id,
            "overwrite_id": overwrite_id,
        }
