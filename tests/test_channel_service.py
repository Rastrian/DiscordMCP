# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import DiscordChannel
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.channel_service import ChannelService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def channel_service(mock_bot, permissions):
    return ChannelService(mock_bot, permissions)


CHANNEL_ID = "234567890123456789"
GUILD_ID = "123456789012345678"


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_get_channel(mock_check, channel_service, mock_bot):
    mock_bot.get_channel.return_value = DiscordChannel(
        id=CHANNEL_ID,
        guild_id=GUILD_ID,
        name="general",
    )
    result = await channel_service.get_channel(CHANNEL_ID, scopes="channel:read")
    assert result["channel_id"] == CHANNEL_ID
    assert result["name"] == "general"
    mock_bot.get_channel.assert_called_once_with(CHANNEL_ID)


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_edit_channel_dry_run(mock_check, channel_service, mock_bot):
    result = await channel_service.edit_channel(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
        name="renamed",
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["channel_id"] == CHANNEL_ID
    mock_bot.modify_channel.assert_not_called()


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_edit_channel_non_dry_run(mock_check, channel_service, mock_bot):
    mock_bot.modify_channel.return_value = DiscordChannel(
        id=CHANNEL_ID,
        guild_id=GUILD_ID,
        name="renamed",
    )
    result = await channel_service.edit_channel(
        CHANNEL_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
        name="renamed",
    )
    assert result["status"] == "updated"
    assert result["dry_run"] is False
    assert result["channel_id"] == CHANNEL_ID
    assert result["name"] == "renamed"
    mock_bot.modify_channel.assert_called_once_with(CHANNEL_ID, name="renamed")


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_edit_permissions_dry_run(mock_check, channel_service, mock_bot):
    result = await channel_service.edit_permissions(
        CHANNEL_ID,
        GUILD_ID,
        overwrite_id="111111111111111111",
        allow="0",
        deny="0",
        overwrite_type=0,
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["channel_id"] == CHANNEL_ID
    assert result["overwrite_id"] == "111111111111111111"
    mock_bot.edit_channel_permissions.assert_not_called()


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_edit_permissions_non_dry_run(mock_check, channel_service, mock_bot):
    result = await channel_service.edit_permissions(
        CHANNEL_ID,
        GUILD_ID,
        overwrite_id="111111111111111111",
        allow="1",
        deny="0",
        overwrite_type=0,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "updated"
    assert result["dry_run"] is False
    assert result["channel_id"] == CHANNEL_ID
    assert result["overwrite_id"] == "111111111111111111"
    mock_bot.edit_channel_permissions.assert_called_once_with(
        CHANNEL_ID,
        "111111111111111111",
        "1",
        "0",
        0,
    )


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_delete_permissions_dry_run(mock_check, channel_service, mock_bot):
    result = await channel_service.delete_permissions(
        CHANNEL_ID,
        GUILD_ID,
        overwrite_id="111111111111111111",
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["channel_id"] == CHANNEL_ID
    assert result["overwrite_id"] == "111111111111111111"
    mock_bot.delete_channel_permissions.assert_not_called()


@patch("discord_mcp_platform.services.channel_service.check_discord_permission")
async def test_delete_permissions_non_dry_run(mock_check, channel_service, mock_bot):
    result = await channel_service.delete_permissions(
        CHANNEL_ID,
        GUILD_ID,
        overwrite_id="111111111111111111",
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "deleted"
    assert result["dry_run"] is False
    assert result["channel_id"] == CHANNEL_ID
    assert result["overwrite_id"] == "111111111111111111"
    mock_bot.delete_channel_permissions.assert_called_once_with(
        CHANNEL_ID,
        "111111111111111111",
    )
