# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.rest_client import DiscordRestClient
from discord_mcp_platform.discord.permissions import (
    ADMINISTRATOR,
    SEND_MESSAGES,
    check_discord_permission,
    compute_permissions_from_roles,
    has_permission,
)
from discord_mcp_platform.errors import AuthorizationError, DiscordPermissionError, PolicyDeniedError
from discord_mcp_platform.security.policy import PermissionService


def test_guild_allowed_empty_list():
    svc = PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])
    assert svc.check_guild_allowed("123") is True


def test_guild_allowed_in_list():
    svc = PermissionService(allowed_guild_ids=["123", "456"], allowed_channel_ids=[])
    assert svc.check_guild_allowed("123") is True


def test_guild_not_allowed():
    svc = PermissionService(allowed_guild_ids=["123"], allowed_channel_ids=[])
    assert svc.check_guild_allowed("999") is False


def test_channel_allowed_empty_list():
    svc = PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])
    assert svc.check_channel_allowed("123") is True


def test_check_read_with_scope():
    svc = PermissionService([], [])
    svc.check_read("guild:read,channel:read", "guild")


def test_check_read_without_scope():
    svc = PermissionService([], [])
    with pytest.raises(AuthorizationError, match="missing channel:read"):
        svc.check_read("guild:read", "channel")


def test_check_write_with_scope():
    svc = PermissionService([], [])
    svc.check_write("message:write,guild:read", "message")


def test_check_write_without_scope():
    svc = PermissionService([], [])
    with pytest.raises(AuthorizationError, match="missing guild:write"):
        svc.check_write("message:write", "guild")


def test_dangerous_operation_dry_run_ok():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("message.send", dry_run=True, confirmation=None)


def test_dangerous_operation_with_confirmation():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("message.send", dry_run=False, confirmation="yes")


def test_dangerous_operation_blocked():
    svc = PermissionService([], [])
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("message.send", dry_run=False, confirmation=None)


def test_dangerous_operation_not_in_list():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("guild.list", dry_run=False, confirmation=None)


def test_scope_parsing_comma_separated():
    svc = PermissionService([], [])
    svc.check_read("  guild:read , channel:read  , message:read ", "channel")


def test_scope_parsing_single():
    svc = PermissionService([], [])
    svc.check_read("guild:read", "guild")


def test_dangerous_operation_channel_edit():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("channel.edit", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("channel.edit", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("channel.edit", dry_run=False, confirmation=None)


def test_dangerous_operation_role_create():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("role.create", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("role.create", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("role.create", dry_run=False, confirmation=None)


def test_dangerous_operation_role_modify():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("role.modify", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("role.modify", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("role.modify", dry_run=False, confirmation=None)


def test_dangerous_operation_role_delete():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("role.delete", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("role.delete", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("role.delete", dry_run=False, confirmation=None)


def test_dangerous_operation_webhook_execute():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("webhook.execute", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("webhook.execute", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("webhook.execute", dry_run=False, confirmation=None)


def test_dangerous_operation_guild_modify():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("guild.modify", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("guild.modify", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("guild.modify", dry_run=False, confirmation=None)


def test_dangerous_operation_invite_create():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("invite.create", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("invite.create", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("invite.create", dry_run=False, confirmation=None)


def test_dangerous_operation_member_unban():
    svc = PermissionService([], [])
    svc.check_dangerous_operation("member.unban", dry_run=True, confirmation=None)
    svc.check_dangerous_operation("member.unban", dry_run=False, confirmation="yes")
    with pytest.raises(PolicyDeniedError):
        svc.check_dangerous_operation("member.unban", dry_run=False, confirmation=None)


# --- compute_permissions_from_roles ---

GUILD_ROLES = [
    {"id": "222", "name": "BotRole", "permissions": str(SEND_MESSAGES)},
    {"id": "111", "name": "@everyone", "permissions": "0"},
]


def test_everyone_role_identified_by_name_not_position():
    # @everyone is NOT the first role in the list; its perms must still be the base
    perms = compute_permissions_from_roles([], guild_roles=GUILD_ROLES)
    assert perms == 0

    guild_roles_everyone_send = [
        {"id": "222", "name": "BotRole", "permissions": "0"},
        {"id": "111", "name": "@everyone", "permissions": str(SEND_MESSAGES)},
    ]
    perms = compute_permissions_from_roles([], guild_roles=guild_roles_everyone_send)
    assert has_permission(perms, SEND_MESSAGES)


def test_bot_roles_or_ed_on_top_of_everyone_base():
    perms = compute_permissions_from_roles(["222"], guild_roles=GUILD_ROLES)
    assert has_permission(perms, SEND_MESSAGES)


def test_bot_roles_missing_from_guild_contribute_nothing():
    perms = compute_permissions_from_roles(["999"], guild_roles=GUILD_ROLES)
    assert perms == 0


def test_owner_returns_administrator():
    perms = compute_permissions_from_roles([], guild_roles=GUILD_ROLES, is_owner=True)
    assert perms == ADMINISTRATOR


# --- check_discord_permission ---


def _permission_bot() -> AsyncMock:
    bot = AsyncMock(spec=BotRuntime)
    bot.bot_id = "333333333333333333"
    bot.rest = AsyncMock(spec=DiscordRestClient)
    bot.rest.get_guild.return_value = {"owner_id": "111111111111111111"}
    bot.get_member.return_value = {"roles": ["222"]}
    bot.list_roles.return_value = GUILD_ROLES
    return bot


async def test_check_discord_permission_grants_when_role_has_permission():
    bot = _permission_bot()
    await check_discord_permission(bot, "123456789012345678", "message.send")


async def test_check_discord_permission_denies_when_missing():
    bot = _permission_bot()
    bot.get_member.return_value = {"roles": []}  # only @everyone (perms 0) applies
    with pytest.raises(DiscordPermissionError, match="bot lacks permission"):
        await check_discord_permission(bot, "123456789012345678", "message.send")


async def test_check_discord_permission_api_error_fails_closed():
    bot = _permission_bot()
    bot.rest.get_guild.side_effect = RuntimeError("discord api down")
    with pytest.raises(DiscordPermissionError, match="denying message.send"):
        await check_discord_permission(bot, "123456789012345678", "message.send")


async def test_check_discord_permission_unknown_operation_is_noop():
    bot = _permission_bot()
    await check_discord_permission(bot, "123456789012345678", "not.a.mapped.operation")
    bot.rest.get_guild.assert_not_called()
