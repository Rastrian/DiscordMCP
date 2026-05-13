# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import pytest

from discord_mcp_platform.errors import AuthorizationError, PolicyDeniedError
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
