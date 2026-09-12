# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import DiscordInvite
from discord_mcp_platform.errors import AuthorizationError, PolicyDeniedError
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.invite_service import InviteService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def invite_service(mock_bot, permissions):
    return InviteService(mock_bot, permissions)


CHANNEL_ID = "234567890123456789"
GUILD_ID = "123456789012345678"
ROLE_1 = "111111111111111111"
ROLE_2 = "222222222222222222"
USER_1 = "333333333333333333"
USER_2 = "444444444444444444"
INVITE_CODE = "abc123"


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_create_invite_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.create_invite(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["channel_id"] == CHANNEL_ID
    mock_bot.create_invite.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_create_invite_non_dry_run(mock_check, invite_service, mock_bot):
    mock_bot.create_invite.return_value = DiscordInvite(
        code="abc123",
        channel_id=CHANNEL_ID,
        guild_id=GUILD_ID,
    )
    result = await invite_service.create_invite(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "created"
    assert result["dry_run"] is False
    assert result["code"] == "abc123"
    assert result["channel_id"] == CHANNEL_ID
    mock_bot.create_invite.assert_called_once_with(CHANNEL_ID, role_ids=None)


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_create_invite_with_roles_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.create_invite(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
        roles=[ROLE_1, ROLE_2],
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["roles"] == [ROLE_1, ROLE_2]
    mock_bot.create_invite.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_create_invite_with_roles_non_dry_run(mock_check, invite_service, mock_bot):
    mock_bot.create_invite.return_value = DiscordInvite(
        code="abc123",
        channel_id=CHANNEL_ID,
        guild_id=GUILD_ID,
    )
    result = await invite_service.create_invite(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
        roles=[ROLE_1, ROLE_2],
    )
    assert result["status"] == "created"
    assert result["dry_run"] is False
    assert result["roles"] == [ROLE_1, ROLE_2]
    mock_bot.create_invite.assert_called_once_with(CHANNEL_ID, role_ids=[ROLE_1, ROLE_2])


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_create_invite_without_roles(mock_check, invite_service, mock_bot):
    mock_bot.create_invite.return_value = DiscordInvite(
        code="abc123",
        channel_id=CHANNEL_ID,
        guild_id=GUILD_ID,
    )
    result = await invite_service.create_invite(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["roles"] is None
    mock_bot.create_invite.assert_called_once_with(CHANNEL_ID, role_ids=None)


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_list_invites(mock_check, invite_service, mock_bot):
    mock_bot.list_invites.return_value = [
        DiscordInvite(
            code="abc123",
            guild_id=GUILD_ID,
            channel_id=CHANNEL_ID,
            uses=5,
            max_uses=10,
            temporary=False,
        ),
        DiscordInvite(
            code="def456",
            guild_id=GUILD_ID,
            channel_id=CHANNEL_ID,
            uses=0,
            max_uses=0,
            temporary=True,
        ),
    ]
    result = await invite_service.list_invites(GUILD_ID, scopes="guild:read")
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["code"] == "abc123"
    assert result[0]["uses"] == 5
    assert result[0]["temporary"] is False
    assert result[1]["code"] == "def456"
    assert result[1]["temporary"] is True
    mock_bot.list_invites.assert_called_once_with(GUILD_ID)


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_get_invite(mock_check, invite_service, mock_bot):
    mock_bot.get_invite.return_value = DiscordInvite(
        code="abc123",
        guild_id=GUILD_ID,
        channel_id=CHANNEL_ID,
        uses=5,
        max_uses=10,
    )
    result = await invite_service.get_invite("abc123", scopes="guild:read")
    assert result["code"] == "abc123"
    assert result["uses"] == 5
    assert result["max_uses"] == 10
    assert result["channel_id"] == CHANNEL_ID
    mock_bot.get_invite.assert_called_once_with("abc123")


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_delete_invite_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.delete_invite(
        "abc123",
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["code"] == "abc123"
    mock_bot.delete_invite.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_delete_invite_non_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.delete_invite(
        "abc123",
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "deleted"
    assert result["dry_run"] is False
    assert result["code"] == "abc123"
    mock_bot.delete_invite.assert_called_once_with("abc123")


# --- Invite target users ---


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_add_invite_target_user_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.add_invite_target_user(
        INVITE_CODE, GUILD_ID, USER_1, scopes="guild:write", dry_run=True
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["code"] == INVITE_CODE
    assert result["user_id"] == USER_1
    mock_bot.add_invite_target_user.assert_not_called()
    mock_check.assert_awaited_once_with(mock_bot, GUILD_ID, "invite.target.add")


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_add_invite_target_user_confirmed(mock_check, invite_service, mock_bot):
    result = await invite_service.add_invite_target_user(
        INVITE_CODE,
        GUILD_ID,
        USER_1,
        scopes="guild:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "added"
    assert result["dry_run"] is False
    assert result["user_id"] == USER_1
    mock_bot.add_invite_target_user.assert_awaited_once_with(INVITE_CODE, USER_1)


async def test_add_invite_target_user_requires_confirmation(invite_service, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invite_service.add_invite_target_user(
            INVITE_CODE, GUILD_ID, USER_1, scopes="guild:write", dry_run=False
        )
    mock_bot.add_invite_target_user.assert_not_called()


async def test_add_invite_target_user_requires_guild_write_scope(invite_service, mock_bot):
    with pytest.raises(AuthorizationError, match="missing guild:write"):
        await invite_service.add_invite_target_user(
            INVITE_CODE, GUILD_ID, USER_1, scopes="channel:write", dry_run=True
        )
    mock_bot.add_invite_target_user.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_remove_invite_target_user_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.remove_invite_target_user(
        INVITE_CODE, GUILD_ID, USER_1, scopes="guild:write", dry_run=True
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["user_id"] == USER_1
    mock_bot.remove_invite_target_user.assert_not_called()
    mock_check.assert_awaited_once_with(mock_bot, GUILD_ID, "invite.target.remove")


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_remove_invite_target_user_confirmed(mock_check, invite_service, mock_bot):
    result = await invite_service.remove_invite_target_user(
        INVITE_CODE,
        GUILD_ID,
        USER_1,
        scopes="guild:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "removed"
    assert result["dry_run"] is False
    mock_bot.remove_invite_target_user.assert_awaited_once_with(INVITE_CODE, USER_1)


async def test_remove_invite_target_user_requires_confirmation(invite_service, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invite_service.remove_invite_target_user(
            INVITE_CODE, GUILD_ID, USER_1, scopes="guild:write", dry_run=False
        )
    mock_bot.remove_invite_target_user.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_add_invite_target_users_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.bulk_add_invite_target_users(
        INVITE_CODE, GUILD_ID, [USER_1, USER_2], scopes="guild:write", dry_run=True
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["count"] == 2
    mock_bot.bulk_add_invite_target_users.assert_not_called()
    mock_check.assert_awaited_once_with(mock_bot, GUILD_ID, "invite.target.bulk_add")


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_add_invite_target_users_confirmed(mock_check, invite_service, mock_bot):
    result = await invite_service.bulk_add_invite_target_users(
        INVITE_CODE,
        GUILD_ID,
        [USER_1, USER_2],
        scopes="guild:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "bulk_added"
    assert result["dry_run"] is False
    assert result["count"] == 2
    mock_bot.bulk_add_invite_target_users.assert_awaited_once_with(INVITE_CODE, [USER_1, USER_2])


async def test_bulk_add_invite_target_users_requires_confirmation(invite_service, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invite_service.bulk_add_invite_target_users(
            INVITE_CODE, GUILD_ID, [USER_1], scopes="guild:write", dry_run=False
        )
    mock_bot.bulk_add_invite_target_users.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_remove_invite_target_users_dry_run(mock_check, invite_service, mock_bot):
    result = await invite_service.bulk_remove_invite_target_users(
        INVITE_CODE, GUILD_ID, [USER_1, USER_2], scopes="guild:write", dry_run=True
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["count"] == 2
    mock_bot.bulk_remove_invite_target_users.assert_not_called()
    mock_check.assert_awaited_once_with(mock_bot, GUILD_ID, "invite.target.bulk_remove")


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_remove_invite_target_users_confirmed(mock_check, invite_service, mock_bot):
    result = await invite_service.bulk_remove_invite_target_users(
        INVITE_CODE,
        GUILD_ID,
        [USER_1, USER_2],
        scopes="guild:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "bulk_removed"
    assert result["dry_run"] is False
    assert result["count"] == 2
    mock_bot.bulk_remove_invite_target_users.assert_awaited_once_with(INVITE_CODE, [USER_1, USER_2])


async def test_bulk_remove_invite_target_users_requires_confirmation(invite_service, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invite_service.bulk_remove_invite_target_users(
            INVITE_CODE, GUILD_ID, [USER_1], scopes="guild:write", dry_run=False
        )
    mock_bot.bulk_remove_invite_target_users.assert_not_called()
