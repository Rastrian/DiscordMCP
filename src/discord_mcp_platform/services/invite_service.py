# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService

log = get_logger("invite_service")


class InviteService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def create_invite(
        self,
        channel_id: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        roles: list[str] | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("invite.create", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "invite.create")
        if dry_run:
            return {
                "status": "validated",
                "dry_run": True,
                "channel_id": channel_id,
                "roles": roles,
            }
        invite = await self._bot.create_invite(channel_id, role_ids=roles, **kwargs)
        return {
            "status": "created",
            "dry_run": False,
            "code": invite.code,
            "channel_id": invite.channel_id,
            "roles": roles,
        }

    async def list_invites(self, guild_id: str, scopes: str) -> list[dict]:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "invite.list")
        invites = await self._bot.list_invites(guild_id)
        return [
            {"code": i.code, "uses": i.uses, "max_uses": i.max_uses, "temporary": i.temporary}
            for i in invites
        ]

    async def get_invite(self, code: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "guild")
        invite = await self._bot.get_invite(code)
        return {
            "code": invite.code,
            "uses": invite.uses,
            "max_uses": invite.max_uses,
            "channel_id": invite.channel_id,
        }

    async def delete_invite(
        self,
        code: str,
        guild_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "channel")
        self._permissions.check_dangerous_operation("invite.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "invite.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "code": code}
        await self._bot.delete_invite(code)
        return {"status": "deleted", "dry_run": False, "code": code}
