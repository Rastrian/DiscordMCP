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
from discord_mcp_platform.mcp.tools.events import get_handler, get_tools
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.event_service import EventService

GUILD_ID = "123456789012345678"
EVENT_ID = "987654321098765432"
USER_ID = "111111111111111111"
START_TIME = "2026-10-01T18:00:00+00:00"


@pytest.fixture
def mock_bot():
    return AsyncMock(spec=BotRuntime)


@pytest.fixture
def audit():
    return AsyncMock(spec=AuditService)


@pytest.fixture
def event_service(mock_bot):
    return EventService(mock_bot, PermissionService(allowed_guild_ids=[], allowed_channel_ids=[]))


@pytest.fixture
def handler(event_service, audit):
    return get_handler(event_service, audit)


def test_tool_names():
    names = {tool.name for tool in get_tools()}
    assert names == {
        "discord.event.list",
        "discord.event.get",
        "discord.event.create",
        "discord.event.update",
        "discord.event.delete",
        "discord.event.list_users",
    }


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_list(mock_check, handler, mock_bot):
    mock_bot.list_scheduled_events.return_value = [{"id": EVENT_ID, "name": "Community call"}]
    result = await handler("discord.event.list", {"guild_id": GUILD_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload[0]["id"] == EVENT_ID
    mock_bot.list_scheduled_events.assert_awaited_once_with(GUILD_ID)


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_get(mock_check, handler, mock_bot):
    mock_bot.get_scheduled_event.return_value = {"id": EVENT_ID, "name": "Community call"}
    result = await handler("discord.event.get", {"guild_id": GUILD_ID, "event_id": EVENT_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["id"] == EVENT_ID
    mock_bot.get_scheduled_event.assert_awaited_once_with(GUILD_ID, EVENT_ID)


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_list_users(mock_check, handler, mock_bot):
    mock_bot.list_scheduled_event_users.return_value = [
        {"user": {"id": USER_ID}, "guildScheduledEventId": EVENT_ID}
    ]
    result = await handler(
        "discord.event.list_users", {"guild_id": GUILD_ID, "event_id": EVENT_ID, "limit": 50}
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload[0]["user"]["id"] == USER_ID
    mock_bot.list_scheduled_event_users.assert_awaited_once_with(GUILD_ID, EVENT_ID, limit=50)


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_create_dry_run_does_not_call_bot(mock_check, handler, mock_bot, audit):
    result = await handler(
        "discord.event.create",
        {
            "guild_id": GUILD_ID,
            "name": "Community call",
            "scheduled_start_time": START_TIME,
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.create_scheduled_event.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.event.create"
    assert audit.record.call_args.kwargs["guild_id"] == GUILD_ID


async def test_event_create_without_confirmation_rejected(handler, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await handler(
            "discord.event.create",
            {
                "guild_id": GUILD_ID,
                "name": "Community call",
                "scheduled_start_time": START_TIME,
                "dry_run": False,
            },
        )
    mock_bot.create_scheduled_event.assert_not_called()


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_create_confirmed(mock_check, handler, mock_bot):
    mock_bot.create_scheduled_event.return_value = {
        "id": EVENT_ID,
        "name": "Community call",
    }
    result = await handler(
        "discord.event.create",
        {
            "guild_id": GUILD_ID,
            "name": "Community call",
            "description": "Weekly community call",
            "scheduled_start_time": START_TIME,
            "entity_type": 3,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "created"
    assert payload["dry_run"] is False
    assert payload["event_id"] == EVENT_ID
    mock_bot.create_scheduled_event.assert_awaited_once_with(
        GUILD_ID,
        name="Community call",
        scheduled_start_time=START_TIME,
        privacy_level=2,
        description="Weekly community call",
        entity_type=3,
    )


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_update_dry_run_does_not_call_bot(mock_check, handler, mock_bot):
    result = await handler(
        "discord.event.update",
        {"guild_id": GUILD_ID, "event_id": EVENT_ID, "name": "Renamed"},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.update_scheduled_event.assert_not_called()


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_update_confirmed_sends_only_provided_fields(mock_check, handler, mock_bot):
    mock_bot.update_scheduled_event.return_value = {"id": EVENT_ID, "name": "Renamed"}
    result = await handler(
        "discord.event.update",
        {
            "guild_id": GUILD_ID,
            "event_id": EVENT_ID,
            "name": "Renamed",
            "status": 4,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "updated"
    mock_bot.update_scheduled_event.assert_awaited_once_with(
        GUILD_ID, EVENT_ID, name="Renamed", status=4
    )


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_delete_dry_run_does_not_call_bot(mock_check, handler, mock_bot):
    result = await handler("discord.event.delete", {"guild_id": GUILD_ID, "event_id": EVENT_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.delete_scheduled_event.assert_not_called()


@patch("discord_mcp_platform.services.event_service.check_discord_permission")
async def test_event_delete_confirmed(mock_check, handler, mock_bot):
    result = await handler(
        "discord.event.delete",
        {
            "guild_id": GUILD_ID,
            "event_id": EVENT_ID,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "deleted"
    assert payload["dry_run"] is False
    mock_bot.delete_scheduled_event.assert_awaited_once_with(GUILD_ID, EVENT_ID)


async def test_unknown_tool_returns_none(handler):
    result = await handler("discord.other.tool", {})
    assert result is None
