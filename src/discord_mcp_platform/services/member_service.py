# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService


class MemberService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def get_member(self, guild_id: str, user_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "member")
        await check_discord_permission(self._bot, guild_id, "guild.read")
        return await self._bot.get_member(guild_id, user_id)

    async def list_members(self, guild_id: str, scopes: str, limit: int = 100) -> list[dict]:
        self._permissions.check_read(scopes, "member")
        await check_discord_permission(self._bot, guild_id, "guild.read")
        return await self._bot.list_members(guild_id, limit=limit)

    async def kick_member(
        self,
        guild_id: str,
        user_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "member")
        self._permissions.check_dangerous_operation("member.kick", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "member.kick")
        if dry_run:
            return {"status": "validated", "dry_run": True}
        await self._bot.kick_member(guild_id, user_id)
        return {"status": "kicked", "dry_run": False, "user_id": user_id}

    async def ban_member(
        self,
        guild_id: str,
        user_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        delete_message_days: int = 0,
    ) -> dict:
        self._permissions.check_write(scopes, "member")
        self._permissions.check_dangerous_operation("member.ban", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "member.ban")
        if dry_run:
            return {"status": "validated", "dry_run": True}
        await self._bot.ban_member(guild_id, user_id, delete_message_days=delete_message_days)
        return {"status": "banned", "dry_run": False, "user_id": user_id}

    async def timeout_member(
        self,
        guild_id: str,
        user_id: str,
        duration_seconds: int,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "member")
        self._permissions.check_dangerous_operation("member.timeout", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "member.timeout")
        if dry_run:
            return {
                "status": "validated",
                "dry_run": True,
                "user_id": user_id,
                "duration_seconds": duration_seconds,
            }
        import datetime

        until = (
            datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(seconds=duration_seconds)
        ).isoformat()
        await self._bot.timeout_member(guild_id, user_id, until)
        return {
            "status": "timed_out",
            "dry_run": False,
            "user_id": user_id,
            "communication_disabled_until": until,
        }

    async def unban_member(
        self,
        guild_id: str,
        user_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "member")
        self._permissions.check_dangerous_operation("member.unban", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "member.unban")
        if dry_run:
            return {"status": "validated", "dry_run": True, "user_id": user_id}
        await self._bot.unban_member(guild_id, user_id)
        return {"status": "unbanned", "dry_run": False, "user_id": user_id}
