# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.errors import PolicyDeniedError
from discord_mcp_platform.mcp.tools.automod import get_handler, get_tools
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.automod_service import AutomodService

GUILD_ID = "123456789012345678"
RULE_ID = "987654321098765432"

TRIGGER = {"keyword_filter": ["spam"], "allow_list": []}
ACTIONS = [{"type": 1, "metadata": {"channel_id": "111111111111111111"}}]


@pytest.fixture
def mock_bot():
    return AsyncMock(spec=BotRuntime)


@pytest.fixture
def audit():
    return AsyncMock(spec=AuditService)


@pytest.fixture
def automod_service(mock_bot):
    return AutomodService(mock_bot, PermissionService(allowed_guild_ids=[], allowed_channel_ids=[]))


@pytest.fixture
def handler(automod_service, audit):
    return get_handler(automod_service, audit)


def test_tool_names():
    names = {tool.name for tool in get_tools()}
    assert names == {
        "discord.automod.list",
        "discord.automod.get",
        "discord.automod.create",
        "discord.automod.update",
        "discord.automod.delete",
    }


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_list(mock_check, handler, mock_bot):
    mock_bot.list_auto_mod_rules.return_value = [{"id": RULE_ID, "name": "block spam"}]
    result = await handler("discord.automod.list", {"guild_id": GUILD_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload[0]["id"] == RULE_ID
    mock_bot.list_auto_mod_rules.assert_awaited_once_with(GUILD_ID)


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_get(mock_check, handler, mock_bot):
    mock_bot.get_auto_mod_rule.return_value = {"id": RULE_ID, "name": "block spam"}
    result = await handler("discord.automod.get", {"guild_id": GUILD_ID, "rule_id": RULE_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["id"] == RULE_ID
    mock_bot.get_auto_mod_rule.assert_awaited_once_with(GUILD_ID, RULE_ID)


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_create_dry_run_does_not_call_bot(mock_check, handler, mock_bot, audit):
    result = await handler(
        "discord.automod.create",
        {
            "guild_id": GUILD_ID,
            "name": "block spam",
            "event_type": 1,
            "trigger": TRIGGER,
            "actions": ACTIONS,
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.create_auto_mod_rule.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.automod.create"
    assert audit.record.call_args.kwargs["guild_id"] == GUILD_ID


async def test_automod_create_without_confirmation_rejected(handler, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await handler(
            "discord.automod.create",
            {
                "guild_id": GUILD_ID,
                "name": "block spam",
                "event_type": 1,
                "trigger": TRIGGER,
                "actions": ACTIONS,
                "dry_run": False,
            },
        )
    mock_bot.create_auto_mod_rule.assert_not_called()


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_create_confirmed(mock_check, handler, mock_bot):
    mock_bot.create_auto_mod_rule.return_value = {"id": RULE_ID, "name": "block spam"}
    result = await handler(
        "discord.automod.create",
        {
            "guild_id": GUILD_ID,
            "name": "block spam",
            "event_type": 1,
            "trigger": TRIGGER,
            "actions": ACTIONS,
            "enabled": False,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "created"
    assert payload["dry_run"] is False
    assert payload["rule_id"] == RULE_ID
    mock_bot.create_auto_mod_rule.assert_awaited_once_with(
        GUILD_ID,
        name="block spam",
        event_type=1,
        trigger=TRIGGER,
        actions=ACTIONS,
        enabled=False,
    )


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_update_dry_run_does_not_call_bot(mock_check, handler, mock_bot):
    result = await handler(
        "discord.automod.update",
        {"guild_id": GUILD_ID, "rule_id": RULE_ID, "enabled": False},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.update_auto_mod_rule.assert_not_called()


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_update_confirmed_sends_only_provided_fields(mock_check, handler, mock_bot):
    mock_bot.update_auto_mod_rule.return_value = {"id": RULE_ID, "name": "block spam"}
    result = await handler(
        "discord.automod.update",
        {
            "guild_id": GUILD_ID,
            "rule_id": RULE_ID,
            "name": "block spam v2",
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "updated"
    mock_bot.update_auto_mod_rule.assert_awaited_once_with(GUILD_ID, RULE_ID, name="block spam v2")


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_delete_dry_run_does_not_call_bot(mock_check, handler, mock_bot):
    result = await handler("discord.automod.delete", {"guild_id": GUILD_ID, "rule_id": RULE_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.delete_auto_mod_rule.assert_not_called()


@patch("discord_mcp_platform.services.automod_service.check_discord_permission")
async def test_automod_delete_confirmed(mock_check, handler, mock_bot):
    result = await handler(
        "discord.automod.delete",
        {
            "guild_id": GUILD_ID,
            "rule_id": RULE_ID,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "deleted"
    assert payload["dry_run"] is False
    mock_bot.delete_auto_mod_rule.assert_awaited_once_with(GUILD_ID, RULE_ID)


async def test_unknown_tool_returns_none(handler):
    result = await handler("discord.other.tool", {})
    assert result is None
