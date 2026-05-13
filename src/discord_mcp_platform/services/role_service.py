# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService


class RoleService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def list_roles(self, guild_id: str, scopes: str) -> list[dict]:
        self._permissions.check_read(scopes, "role")
        await check_discord_permission(self._bot, guild_id, "role.read")
        return await self._bot.list_roles(guild_id)

    async def add_role(
        self,
        guild_id: str,
        user_id: str,
        role_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "role")
        self._permissions.check_dangerous_operation("role.assign", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "role.assign")
        if dry_run:
            return {"status": "validated", "dry_run": True}
        await self._bot.add_role(guild_id, user_id, role_id)
        return {"status": "assigned", "dry_run": False}

    async def remove_role(
        self,
        guild_id: str,
        user_id: str,
        role_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "role")
        self._permissions.check_dangerous_operation("role.remove", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "role.assign")
        if dry_run:
            return {"status": "validated", "dry_run": True}
        await self._bot.remove_role(guild_id, user_id, role_id)
        return {"status": "removed", "dry_run": False}

    async def create_role(
        self,
        guild_id: str,
        name: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "role")
        self._permissions.check_dangerous_operation("role.create", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "role.create")
        if dry_run:
            return {"status": "validated", "dry_run": True, "name": name}
        role = await self._bot.create_role(guild_id, name=name, **kwargs)
        return {"status": "created", "dry_run": False, "role_id": role.id, "name": role.name}

    async def modify_role(
        self,
        guild_id: str,
        role_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "role")
        self._permissions.check_dangerous_operation("role.modify", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "role.modify")
        if dry_run:
            return {"status": "validated", "dry_run": True, "role_id": role_id}
        role = await self._bot.modify_role(guild_id, role_id, **kwargs)
        return {"status": "updated", "dry_run": False, "role_id": role.id, "name": role.name}

    async def delete_role(
        self,
        guild_id: str,
        role_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "role")
        self._permissions.check_dangerous_operation("role.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "role.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "role_id": role_id}
        await self._bot.delete_role(guild_id, role_id)
        return {"status": "deleted", "dry_run": False, "role_id": role_id}

    async def reorder_roles(self, guild_id: str, positions: list[dict], scopes: str) -> list[dict]:
        self._permissions.check_write(scopes, "role")
        await check_discord_permission(self._bot, guild_id, "role.modify")
        roles = await self._bot.reorder_roles(guild_id, positions)
        return [{"role_id": r.id, "name": r.name, "position": r.position} for r in roles]
