# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from discord_mcp_platform.discord.models import DiscordMessage, MessageSendInput
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.message_service import MessageService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def message_service(mock_bot, permissions):
    return MessageService(mock_bot, permissions)


async def test_send_dry_run_does_not_call_discord(message_service, mock_bot):
    input_data = MessageSendInput(
        guild_id="123456789012345678",
        channel_id="234567890123456789",
        content="Hello",
        dry_run=True,
    )
    result = await message_service.send(input_data, scopes="message:write")
    assert result.status == "validated"
    assert result.dry_run is True
    assert result.message_id is None
    mock_bot.send_message.assert_not_called()


async def test_send_non_dry_run_calls_discord(message_service, mock_bot):
    mock_bot.send_message.return_value = DiscordMessage(
        id="999999999999999999",
        channel_id="234567890123456789",
        author_id="111111111111111111",
        author_name="Bot",
        content="Hello",
        timestamp="2025-01-01T00:00:00Z",
    )
    input_data = MessageSendInput(
        guild_id="123456789012345678",
        channel_id="234567890123456789",
        content="Hello",
        dry_run=False,
        confirmation="yes",
    )
    result = await message_service.send(input_data, scopes="message:write")
    assert result.status == "sent"
    assert result.dry_run is False
    assert result.message_id == "999999999999999999"
    mock_bot.send_message.assert_called_once_with("234567890123456789", "Hello")
