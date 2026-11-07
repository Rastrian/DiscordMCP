# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.mcp.tools.permissions import get_handler, get_tools
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.permission_query_service import PermissionQueryService

GUILD_ID = "123456789012345678"
CHANNEL_ID = "222222222222222222"
USER_ID = "111111111111111111"
ROLE_ID = "333333333333333333"
PERMISSIONS = {"permissions": "137457699711"}


@pytest.fixture
def mock_bot():
    return AsyncMock(spec=BotRuntime)


@pytest.fixture
def audit():
    return AsyncMock(spec=AuditService)


@pytest.fixture
def permission_service(mock_bot):
    return PermissionQueryService(
        mock_bot, PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])
    )


@pytest.fixture
def handler(permission_service, audit):
    return get_handler(permission_service, audit)


def test_tool_names():
    names = {tool.name for tool in get_tools()}
    assert names == {
        "discord.permissions.get_guild_member",
        "discord.permissions.get_guild_role",
        "discord.permissions.get_channel_member",
        "discord.permissions.get_channel_role",
    }


@patch("discord_mcp_platform.services.permission_query_service.check_discord_permission")
async def test_guild_member_permissions(mock_check, handler, mock_bot, audit):
    mock_bot.get_guild_member_permissions.return_value = PERMISSIONS
    result = await handler(
        "discord.permissions.get_guild_member", {"guild_id": GUILD_ID, "user_id": USER_ID}
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload == PERMISSIONS
    mock_bot.get_guild_member_permissions.assert_awaited_once_with(GUILD_ID, USER_ID)
    mock_check.assert_awaited_once_with(mock_bot, GUILD_ID, "permissions.read")
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.permissions.get_guild_member"
    assert audit.record.call_args.kwargs["guild_id"] == GUILD_ID


@patch("discord_mcp_platform.services.permission_query_service.check_discord_permission")
async def test_guild_role_permissions(mock_check, handler, mock_bot):
    mock_bot.get_guild_role_permissions.return_value = PERMISSIONS
    result = await handler(
        "discord.permissions.get_guild_role", {"guild_id": GUILD_ID, "role_id": ROLE_ID}
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload == PERMISSIONS
    mock_bot.get_guild_role_permissions.assert_awaited_once_with(GUILD_ID, ROLE_ID)
    mock_check.assert_awaited_once_with(mock_bot, GUILD_ID, "permissions.read")


@patch("discord_mcp_platform.services.permission_query_service.check_discord_permission")
async def test_channel_member_permissions(mock_check, handler, mock_bot, audit):
    mock_bot.get_channel_member_permissions.return_value = PERMISSIONS
    result = await handler(
        "discord.permissions.get_channel_member", {"channel_id": CHANNEL_ID, "user_id": USER_ID}
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload == PERMISSIONS
    mock_bot.get_channel_member_permissions.assert_awaited_once_with(CHANNEL_ID, USER_ID)
    mock_check.assert_awaited_once_with(
        mock_bot, mock_bot.get_channel.return_value.guild_id, "permissions.channel_read"
    )
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.permissions.get_channel_member"
    assert audit.record.call_args.kwargs["channel_id"] == CHANNEL_ID


@patch("discord_mcp_platform.services.permission_query_service.check_discord_permission")
async def test_channel_role_permissions(mock_check, handler, mock_bot):
    mock_bot.get_channel_role_permissions.return_value = PERMISSIONS
    result = await handler(
        "discord.permissions.get_channel_role", {"channel_id": CHANNEL_ID, "role_id": ROLE_ID}
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload == PERMISSIONS
    mock_bot.get_channel_role_permissions.assert_awaited_once_with(CHANNEL_ID, ROLE_ID)
    mock_check.assert_awaited_once_with(
        mock_bot, mock_bot.get_channel.return_value.guild_id, "permissions.channel_read"
    )


async def test_short_snowflake_rejected(handler, mock_bot):
    with pytest.raises(ValidationError):
        await handler(
            "discord.permissions.get_guild_member", {"guild_id": GUILD_ID, "user_id": "12345"}
        )
    mock_bot.get_guild_member_permissions.assert_not_called()


async def test_unknown_tool_returns_none(handler):
    result = await handler("discord.other.tool", {})
    assert result is None
