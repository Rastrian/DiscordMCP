# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import DiscordInvite
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
    mock_bot.create_invite.assert_called_once_with(CHANNEL_ID)


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
