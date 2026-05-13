# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock

from discord_mcp_platform.discord.models import DiscordGuild, GuildListInput
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.guild_service import GuildService


async def test_list_guilds_with_mocked_discord():
    mock_bot = AsyncMock(spec=BotRuntime)
    mock_bot.list_guilds.return_value = [
        DiscordGuild(id="111", name="Guild A", owner=False),
        DiscordGuild(id="222", name="Guild B", owner=True),
    ]
    permissions = PermissionService([], [])
    svc = GuildService(mock_bot, permissions)

    result = await svc.list_guilds(GuildListInput(), scopes="guild:read")
    assert len(result.guilds) == 2
    assert result.guilds[0].name == "Guild A"
    assert result.guilds[1].id == "222"
    mock_bot.list_guilds.assert_called_once()
