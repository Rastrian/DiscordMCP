# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import DiscordGuild
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.guild_service import GuildService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def guild_service(mock_bot, permissions):
    return GuildService(mock_bot, permissions)


GUILD_ID = "123456789012345678"


@patch("discord_mcp_platform.services.guild_service.check_discord_permission")
async def test_get_guild(mock_check, guild_service, mock_bot):
    mock_bot.get_guild.return_value = DiscordGuild(
        id=GUILD_ID,
        name="Test Guild",
        icon="iconhash123",
    )
    result = await guild_service.get_guild(GUILD_ID, scopes="guild:read")
    assert result["guild_id"] == GUILD_ID
    assert result["name"] == "Test Guild"
    assert result["icon"] == "iconhash123"
    mock_bot.get_guild.assert_called_once_with(GUILD_ID)


@patch("discord_mcp_platform.services.guild_service.check_discord_permission")
async def test_modify_guild_dry_run(mock_check, guild_service, mock_bot):
    result = await guild_service.modify_guild(
        GUILD_ID,
        scopes="guild:write",
        dry_run=True,
        name="New Name",
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["guild_id"] == GUILD_ID
    mock_bot.modify_guild.assert_not_called()


@patch("discord_mcp_platform.services.guild_service.check_discord_permission")
async def test_modify_guild_non_dry_run(mock_check, guild_service, mock_bot):
    mock_bot.modify_guild.return_value = DiscordGuild(
        id=GUILD_ID,
        name="New Name",
        icon="iconhash123",
    )
    result = await guild_service.modify_guild(
        GUILD_ID,
        scopes="guild:write",
        dry_run=False,
        confirmation="yes",
        name="New Name",
    )
    assert result["status"] == "updated"
    assert result["dry_run"] is False
    assert result["guild_id"] == GUILD_ID
    assert result["name"] == "New Name"
    mock_bot.modify_guild.assert_called_once_with(GUILD_ID, name="New Name")
