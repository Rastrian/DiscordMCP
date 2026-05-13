# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import DiscordWebhook
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.webhook_service import WebhookService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def webhook_service(mock_bot, permissions):
    return WebhookService(mock_bot, permissions)


CHANNEL_ID = "234567890123456789"
GUILD_ID = "123456789012345678"
WEBHOOK_ID = "345678901234567890"


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_create_webhook_dry_run(mock_check, webhook_service, mock_bot):
    result = await webhook_service.create_webhook(
        CHANNEL_ID,
        "TestHook",
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["name"] == "TestHook"
    mock_bot.create_webhook.assert_not_called()


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_create_webhook_non_dry_run(mock_check, webhook_service, mock_bot):
    mock_bot.create_webhook.return_value = {"id": WEBHOOK_ID, "name": "TestHook"}
    result = await webhook_service.create_webhook(
        CHANNEL_ID,
        "TestHook",
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "created"
    assert result["dry_run"] is False
    assert result["webhook_id"] == WEBHOOK_ID
    assert result["name"] == "TestHook"
    mock_bot.create_webhook.assert_called_once_with(CHANNEL_ID, "TestHook")


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_list_webhooks(mock_check, webhook_service, mock_bot):
    mock_bot.list_webhooks.return_value = [
        {"id": WEBHOOK_ID, "name": "Hook1", "channel_id": CHANNEL_ID},
        {"id": "456789012345678901", "name": "Hook2", "channel_id": CHANNEL_ID},
    ]
    result = await webhook_service.list_webhooks(GUILD_ID, scopes="channel:read")
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["webhook_id"] == WEBHOOK_ID
    assert result[0]["name"] == "Hook1"
    assert result[1]["webhook_id"] == "456789012345678901"
    mock_bot.list_webhooks.assert_called_once_with(GUILD_ID)


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_get_webhook(mock_check, webhook_service, mock_bot):
    mock_bot.get_webhook.return_value = DiscordWebhook(
        id=WEBHOOK_ID,
        channel_id=CHANNEL_ID,
        guild_id=GUILD_ID,
        name="Hook1",
    )
    result = await webhook_service.get_webhook(WEBHOOK_ID, GUILD_ID, scopes="channel:read")
    assert result["webhook_id"] == WEBHOOK_ID
    assert result["name"] == "Hook1"
    assert result["channel_id"] == CHANNEL_ID
    mock_bot.get_webhook.assert_called_once_with(WEBHOOK_ID)


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_modify_webhook_dry_run(mock_check, webhook_service, mock_bot):
    result = await webhook_service.modify_webhook(
        WEBHOOK_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["webhook_id"] == WEBHOOK_ID
    mock_bot.modify_webhook.assert_not_called()


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_modify_webhook_non_dry_run(mock_check, webhook_service, mock_bot):
    mock_bot.modify_webhook.return_value = DiscordWebhook(
        id=WEBHOOK_ID,
        channel_id=CHANNEL_ID,
        guild_id=GUILD_ID,
        name="RenamedHook",
    )
    result = await webhook_service.modify_webhook(
        WEBHOOK_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
        name="RenamedHook",
    )
    assert result["status"] == "updated"
    assert result["dry_run"] is False
    assert result["webhook_id"] == WEBHOOK_ID
    assert result["name"] == "RenamedHook"
    mock_bot.modify_webhook.assert_called_once_with(WEBHOOK_ID, name="RenamedHook")


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_delete_webhook_dry_run(mock_check, webhook_service, mock_bot):
    result = await webhook_service.delete_webhook(
        WEBHOOK_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["webhook_id"] == WEBHOOK_ID
    mock_bot.delete_webhook.assert_not_called()


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_delete_webhook_non_dry_run(mock_check, webhook_service, mock_bot):
    result = await webhook_service.delete_webhook(
        WEBHOOK_ID,
        GUILD_ID,
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "deleted"
    assert result["dry_run"] is False
    assert result["webhook_id"] == WEBHOOK_ID
    mock_bot.delete_webhook.assert_called_once_with(WEBHOOK_ID)


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_execute_webhook_dry_run(mock_check, webhook_service, mock_bot):
    result = await webhook_service.execute_webhook(
        WEBHOOK_ID,
        "token123",
        GUILD_ID,
        content="Hello",
        scopes="channel:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["webhook_id"] == WEBHOOK_ID
    mock_bot.execute_webhook.assert_not_called()


@patch("discord_mcp_platform.services.webhook_service.check_discord_permission")
async def test_execute_webhook_non_dry_run(mock_check, webhook_service, mock_bot):
    mock_bot.execute_webhook.return_value = {"id": "567890123456789012"}
    result = await webhook_service.execute_webhook(
        WEBHOOK_ID,
        "token123",
        GUILD_ID,
        content="Hello",
        scopes="channel:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "sent"
    assert result["dry_run"] is False
    assert result["message_id"] == "567890123456789012"
    mock_bot.execute_webhook.assert_called_once_with(
        WEBHOOK_ID,
        "token123",
        content="Hello",
    )
