# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import DiscordRole
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.role_service import RoleService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    return bot


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def role_service(mock_bot, permissions):
    return RoleService(mock_bot, permissions)


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_list_roles(mock_check, role_service, mock_bot):
    mock_bot.list_roles.return_value = [
        {"id": "111111111111111111", "name": "Admin", "position": 1},
        {"id": "222222222222222222", "name": "Member", "position": 2},
    ]
    result = await role_service.list_roles("123456789012345678", scopes="role:read")
    assert isinstance(result, list)
    assert len(result) == 2
    mock_bot.list_roles.assert_called_once_with("123456789012345678")


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_create_role_dry_run(mock_check, role_service, mock_bot):
    result = await role_service.create_role(
        "123456789012345678",
        name="TestRole",
        scopes="role:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["name"] == "TestRole"
    mock_bot.create_role.assert_not_called()


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_create_role_non_dry_run(mock_check, role_service, mock_bot):
    mock_bot.create_role.return_value = DiscordRole(
        id="111",
        guild_id="123456789012345678",
        name="TestRole",
    )
    result = await role_service.create_role(
        "123456789012345678",
        name="TestRole",
        scopes="role:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "created"
    assert result["dry_run"] is False
    assert result["role_id"] == "111"
    assert result["name"] == "TestRole"
    mock_bot.create_role.assert_called_once_with("123456789012345678", name="TestRole")


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_modify_role_dry_run(mock_check, role_service, mock_bot):
    result = await role_service.modify_role(
        "123456789012345678",
        "222222222222222222",
        scopes="role:write",
        dry_run=True,
        name="RenamedRole",
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["role_id"] == "222222222222222222"
    mock_bot.modify_role.assert_not_called()


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_modify_role_non_dry_run(mock_check, role_service, mock_bot):
    mock_bot.modify_role.return_value = DiscordRole(
        id="222222222222222222",
        guild_id="123456789012345678",
        name="RenamedRole",
    )
    result = await role_service.modify_role(
        "123456789012345678",
        "222222222222222222",
        scopes="role:write",
        dry_run=False,
        confirmation="yes",
        name="RenamedRole",
    )
    assert result["status"] == "updated"
    assert result["dry_run"] is False
    assert result["role_id"] == "222222222222222222"
    assert result["name"] == "RenamedRole"
    mock_bot.modify_role.assert_called_once_with(
        "123456789012345678",
        "222222222222222222",
        name="RenamedRole",
    )


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_delete_role_dry_run(mock_check, role_service, mock_bot):
    result = await role_service.delete_role(
        "123456789012345678",
        "333333333333333333",
        scopes="role:write",
        dry_run=True,
    )
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["role_id"] == "333333333333333333"
    mock_bot.delete_role.assert_not_called()


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_delete_role_non_dry_run(mock_check, role_service, mock_bot):
    result = await role_service.delete_role(
        "123456789012345678",
        "333333333333333333",
        scopes="role:write",
        dry_run=False,
        confirmation="yes",
    )
    assert result["status"] == "deleted"
    assert result["dry_run"] is False
    assert result["role_id"] == "333333333333333333"
    mock_bot.delete_role.assert_called_once_with("123456789012345678", "333333333333333333")


@patch("discord_mcp_platform.services.role_service.check_discord_permission")
async def test_reorder_roles(mock_check, role_service, mock_bot):
    mock_bot.reorder_roles.return_value = [
        DiscordRole(
            id="111111111111111111", guild_id="123456789012345678", name="Admin", position=0
        ),
        DiscordRole(id="222222222222222222", guild_id="123456789012345678", name="Mod", position=1),
    ]
    positions = [
        {"id": "111111111111111111", "position": 0},
        {"id": "222222222222222222", "position": 1},
    ]
    result = await role_service.reorder_roles("123456789012345678", positions, scopes="role:write")
    assert len(result) == 2
    assert result[0]["role_id"] == "111111111111111111"
    assert result[0]["name"] == "Admin"
    assert result[0]["position"] == 0
    assert result[1]["role_id"] == "222222222222222222"
    assert result[1]["position"] == 1
    mock_bot.reorder_roles.assert_called_once_with("123456789012345678", positions)
