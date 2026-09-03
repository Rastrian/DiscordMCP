# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.permissions import check_discord_permission
from discord_mcp_platform.security.policy import PermissionService


class AutomodService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def list_rules(self, guild_id: str, scopes: str) -> list[dict]:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "automod.read")
        return await self._bot.list_auto_mod_rules(guild_id)

    async def get_rule(self, guild_id: str, rule_id: str, scopes: str) -> dict:
        self._permissions.check_read(scopes, "guild")
        await check_discord_permission(self._bot, guild_id, "automod.read")
        return await self._bot.get_auto_mod_rule(guild_id, rule_id)

    async def create_rule(
        self,
        guild_id: str,
        name: str,
        event_type: int,
        trigger: dict,
        actions: list[dict],
        scopes: str,
        enabled: bool = True,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("automod.create", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "automod.create")
        if dry_run:
            return {"status": "validated", "dry_run": True, "name": name}
        rule = await self._bot.create_auto_mod_rule(
            guild_id,
            name=name,
            event_type=event_type,
            trigger=trigger,
            actions=actions,
            enabled=enabled,
        )
        return {
            "status": "created",
            "dry_run": False,
            "rule_id": rule["id"],
            "name": rule.get("name", name),
        }

    async def update_rule(
        self,
        guild_id: str,
        rule_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
        **kwargs,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("automod.update", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "automod.update")
        if dry_run:
            return {"status": "validated", "dry_run": True, "rule_id": rule_id}
        rule = await self._bot.update_auto_mod_rule(guild_id, rule_id, **kwargs)
        return {"status": "updated", "dry_run": False, "rule_id": rule["id"]}

    async def delete_rule(
        self,
        guild_id: str,
        rule_id: str,
        scopes: str,
        dry_run: bool = True,
        confirmation: str | None = None,
    ) -> dict:
        self._permissions.check_write(scopes, "guild")
        self._permissions.check_dangerous_operation("automod.delete", dry_run, confirmation)
        await check_discord_permission(self._bot, guild_id, "automod.delete")
        if dry_run:
            return {"status": "validated", "dry_run": True, "rule_id": rule_id}
        await self._bot.delete_auto_mod_rule(guild_id, rule_id)
        return {"status": "deleted", "dry_run": False, "rule_id": rule_id}
