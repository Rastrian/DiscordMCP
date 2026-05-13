# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.member_service import MemberService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def member_service(mock_bot, permissions):
    return MemberService(mock_bot, permissions)


GUILD_ID = "123456789012345678"
USER_ID = "987654321098765432"


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_get_member(mock_check, member_service, mock_bot):
    mock_bot.get_member.return_value = {
        "user_id": USER_ID,
        "nick": "TestUser",
        "roles": ["111111111111111111"],
    }
    result = await member_service.get_member(GUILD_ID, USER_ID, scopes="member:read")
    assert result["user_id"] == USER_ID
    mock_bot.get_member.assert_called_once_with(GUILD_ID, USER_ID)


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_list_members(mock_check, member_service, mock_bot):
    mock_bot.list_members.return_value = [
        {"user_id": USER_ID, "nick": "TestUser"},
        {"user_id": "111111111111111111", "nick": "OtherUser"},
    ]
    result = await member_service.list_members(GUILD_ID, scopes="member:read")
    assert isinstance(result, list)
    assert len(result) == 2
    mock_bot.list_members.assert_called_once_with(GUILD_ID, limit=100)


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_kick_member_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.kick_member(
        GUILD_ID,
        USER_ID,
        scopes="member:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    mock_bot.kick_member.assert_not_called()


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_kick_member_non_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.kick_member(
        GUILD_ID,
        USER_ID,
        scopes="member:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "kicked"
    assert result["dry_run"] is False
    assert result["user_id"] == USER_ID
    mock_bot.kick_member.assert_called_once_with(GUILD_ID, USER_ID)


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_ban_member_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.ban_member(
        GUILD_ID,
        USER_ID,
        scopes="member:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    mock_bot.ban_member.assert_not_called()


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_ban_member_non_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.ban_member(
        GUILD_ID,
        USER_ID,
        scopes="member:write",
        dry_run=False,
        confirmation="yes",
        delete_message_days=1,
    )
    assert result["status"] == "banned"
    assert result["dry_run"] is False
    assert result["user_id"] == USER_ID
    mock_bot.ban_member.assert_called_once_with(GUILD_ID, USER_ID, delete_message_days=1)


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_timeout_member_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.timeout_member(
        GUILD_ID,
        USER_ID,
        duration_seconds=600,
        scopes="member:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["user_id"] == USER_ID
    assert result["duration_seconds"] == 600
    mock_bot.timeout_member.assert_not_called()


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_timeout_member_non_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.timeout_member(
        GUILD_ID,
        USER_ID,
        duration_seconds=600,
        scopes="member:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "timed_out"
    assert result["dry_run"] is False
    assert result["user_id"] == USER_ID
    assert result["communication_disabled_until"] is not None
    mock_bot.timeout_member.assert_called_once()
    call_args = mock_bot.timeout_member.call_args
    assert call_args[0][0] == GUILD_ID
    assert call_args[0][1] == USER_ID


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_unban_member_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.unban_member(
        GUILD_ID,
        USER_ID,
        scopes="member:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["user_id"] == USER_ID
    mock_bot.unban_member.assert_not_called()


@patch("discord_mcp_platform.services.member_service.check_discord_permission")
async def test_unban_member_non_dry_run(mock_check, member_service, mock_bot):
    result = await member_service.unban_member(
        GUILD_ID,
        USER_ID,
        scopes="member:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "unbanned"
    assert result["dry_run"] is False
    assert result["user_id"] == USER_ID
    mock_bot.unban_member.assert_called_once_with(GUILD_ID, USER_ID)
