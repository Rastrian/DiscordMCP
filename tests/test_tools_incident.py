# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.rest_client import DISCORD_API_BASE, DiscordRestClient
from discord_mcp_platform.errors import PolicyDeniedError
from discord_mcp_platform.mcp.tools.guilds import get_handler, get_tools
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.guild_service import GuildService

GUILD_ID = "123456789012345678"
MAX_DURATION = 86400


@pytest.fixture
def mock_bot():
    return AsyncMock(spec=BotRuntime)


@pytest.fixture
def audit():
    return AsyncMock(spec=AuditService)


@pytest.fixture
def guild_service(mock_bot):
    return GuildService(mock_bot, PermissionService(allowed_guild_ids=[], allowed_channel_ids=[]))


@pytest.fixture
def handler(guild_service, audit):
    return get_handler(guild_service, audit)


# --- Timestamp helper ---


def test_incident_timestamp_rejects_duration_over_24h():
    with pytest.raises(ValueError):
        GuildService.incident_actions_timestamp(90000)


def test_incident_timestamp_rejects_non_positive_duration():
    with pytest.raises(ValueError):
        GuildService.incident_actions_timestamp(0)


def test_incident_timestamp_returns_future_iso():
    before = datetime.now(timezone.utc)
    stamp = GuildService.incident_actions_timestamp(3600)
    parsed = datetime.fromisoformat(stamp)
    assert parsed.tzinfo is not None
    assert parsed <= before + timedelta(seconds=3600) + timedelta(seconds=5)
    assert parsed >= before + timedelta(seconds=3590)


def test_incident_timestamp_accepts_max_24h():
    stamp = GuildService.incident_actions_timestamp(MAX_DURATION)
    assert datetime.fromisoformat(stamp) > datetime.now(timezone.utc)


# --- Tool dispatch ---


def test_incident_tool_registered():
    names = {tool.name for tool in get_tools()}
    assert "discord.guild.incident_actions" in names


@patch("discord_mcp_platform.services.guild_service.check_discord_permission")
async def test_incident_actions_dry_run_does_not_call_bot(mock_check, handler, mock_bot):
    invites = GuildService.incident_actions_timestamp(3600)
    result = await handler(
        "discord.guild.incident_actions",
        {"guild_id": GUILD_ID, "invites_disabled_until": invites},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.set_incident_actions.assert_not_called()


@patch("discord_mcp_platform.services.guild_service.check_discord_permission")
async def test_incident_actions_sends_exact_iso_timestamps(mock_check, handler, mock_bot, audit):
    invites = GuildService.incident_actions_timestamp(3600)
    dms = GuildService.incident_actions_timestamp(MAX_DURATION)
    mock_bot.set_incident_actions.return_value = {
        "invites_disabled_until": invites,
        "dms_disabled_until": dms,
    }
    result = await handler(
        "discord.guild.incident_actions",
        {
            "guild_id": GUILD_ID,
            "invites_disabled_until": invites,
            "dms_disabled_until": dms,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "updated"
    assert payload["dry_run"] is False
    mock_bot.set_incident_actions.assert_awaited_once_with(GUILD_ID, invites, dms)
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.guild.incident_actions"


async def test_incident_actions_without_confirmation_rejected(handler, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await handler(
            "discord.guild.incident_actions",
            {
                "guild_id": GUILD_ID,
                "invites_disabled_until": "2026-09-03T12:00:00+00:00",
                "dry_run": False,
            },
        )
    mock_bot.set_incident_actions.assert_not_called()


async def test_incident_actions_rejects_non_iso_timestamp(handler):
    with pytest.raises(ValueError):
        await handler(
            "discord.guild.incident_actions",
            {"guild_id": GUILD_ID, "invites_disabled_until": "not-a-timestamp"},
        )


@patch("discord_mcp_platform.services.guild_service.check_discord_permission")
async def test_incident_actions_can_re_enable(mock_check, handler, mock_bot):
    mock_bot.set_incident_actions.return_value = {
        "invites_disabled_until": None,
        "dms_disabled_until": None,
    }
    result = await handler(
        "discord.guild.incident_actions",
        {
            "guild_id": GUILD_ID,
            "invites_disabled_until": None,
            "dms_disabled_until": None,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "updated"
    mock_bot.set_incident_actions.assert_awaited_once_with(GUILD_ID, None, None)


# --- REST client body ---


async def test_rest_set_incident_actions_body():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["json"] = json.loads(request.content)
        return httpx.Response(200, json={})

    client = DiscordRestClient("token")
    client._client = httpx.AsyncClient(
        base_url=DISCORD_API_BASE,
        headers={"Authorization": "Bot token"},
        transport=httpx.MockTransport(transport),
    )
    invites = GuildService.incident_actions_timestamp(3600)
    await client.set_incident_actions(GUILD_ID, invites, None)
    await client.close()
    assert seen["method"] == "PUT"
    assert seen["url"] == f"{DISCORD_API_BASE}/guilds/{GUILD_ID}/incident-actions"
    assert seen["json"] == {
        "invites_disabled_until": invites,
        "dms_disabled_until": None,
    }


# --- Registration (B5) ---


async def test_all_new_tools_registered_without_duplicates():
    from mcp.server import Server
    from mcp.types import ListToolsRequest

    from discord_mcp_platform.mcp.tools import register_all_tools

    server = Server("test")
    register_all_tools(
        server,
        guild_service=AsyncMock(),
        channel_service=AsyncMock(),
        message_service=AsyncMock(),
        thread_service=AsyncMock(),
        audit_service=AsyncMock(spec=AuditService),
        automation_service=AsyncMock(),
        role_service=AsyncMock(),
        member_service=AsyncMock(),
        moderation_service=AsyncMock(),
        webhook_service=AsyncMock(),
        invite_service=AsyncMock(),
        event_service=AsyncMock(),
        automod_service=AsyncMock(),
        bot=AsyncMock(spec=BotRuntime),
    )
    response = await server.request_handlers[ListToolsRequest](
        ListToolsRequest(method="tools/list")
    )
    list_result = getattr(response, "root", response)
    names = [tool.name for tool in list_result.tools]
    expected_new = [
        "discord.event.list",
        "discord.event.get",
        "discord.event.create",
        "discord.event.update",
        "discord.event.delete",
        "discord.event.list_users",
        "discord.automod.list",
        "discord.automod.get",
        "discord.automod.create",
        "discord.automod.update",
        "discord.automod.delete",
        "discord.pin.list",
        "discord.pin.add",
        "discord.pin.remove",
        "discord.reaction.list",
        "discord.reaction.remove_user",
        "discord.guild.incident_actions",
    ]
    for name in expected_new:
        assert name in names
    assert len(names) == len(set(names))
