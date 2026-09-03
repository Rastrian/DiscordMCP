# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import httpx
import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.rest_client import DISCORD_API_BASE, DiscordRestClient
from discord_mcp_platform.errors import PolicyDeniedError
from discord_mcp_platform.mcp.tools.channels import get_handler as channel_handler
from discord_mcp_platform.mcp.tools.channels import get_tools as channel_tools
from discord_mcp_platform.mcp.tools.reactions import get_handler as reaction_handler
from discord_mcp_platform.mcp.tools.reactions import get_tools as reaction_tools
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.channel_service import ChannelService
from discord_mcp_platform.services.message_service import MessageService

GUILD_ID = "123456789012345678"
CHANNEL_ID = "222222222222222222"
MESSAGE_ID = "333333333333333333"
USER_ID = "111111111111111111"
EMOJI = "👍"
EMOJI_ENCODED = "%F0%9F%91%8D"


@pytest.fixture
def mock_bot():
    return AsyncMock(spec=BotRuntime)


@pytest.fixture
def audit():
    return AsyncMock(spec=AuditService)


@pytest.fixture
def permissions():
    return PermissionService(allowed_guild_ids=[], allowed_channel_ids=[])


@pytest.fixture
def channel_service(mock_bot, permissions):
    return ChannelService(mock_bot, permissions)


@pytest.fixture
def message_service(mock_bot, permissions):
    return MessageService(mock_bot, permissions)


@pytest.fixture
def channels(channel_service, audit):
    return channel_handler(channel_service, audit)


@pytest.fixture
def reactions(message_service, audit):
    return reaction_handler(message_service, audit)


def test_pin_tool_names():
    names = {tool.name for tool in channel_tools()}
    assert {"discord.pin.list", "discord.pin.add", "discord.pin.remove"} <= names


def test_reaction_tool_names():
    names = {tool.name for tool in reaction_tools()}
    assert {"discord.reaction.list", "discord.reaction.remove_user"} <= names


# --- Pins (via ChannelService) ---


async def test_pin_list(channels, mock_bot):
    mock_bot.list_pinned_messages.return_value = [{"id": MESSAGE_ID, "content": "pinned"}]
    result = await channels("discord.pin.list", {"channel_id": CHANNEL_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload[0]["id"] == MESSAGE_ID
    mock_bot.list_pinned_messages.assert_awaited_once_with(CHANNEL_ID)


async def test_pin_add_dry_run_does_not_call_bot(channels, mock_bot, audit):
    result = await channels("discord.pin.add", {"channel_id": CHANNEL_ID, "message_id": MESSAGE_ID})
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.pin_message.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.pin.add"


async def test_pin_add_without_confirmation_rejected(channels, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await channels(
            "discord.pin.add",
            {"channel_id": CHANNEL_ID, "message_id": MESSAGE_ID, "dry_run": False},
        )
    mock_bot.pin_message.assert_not_called()


async def test_pin_add_confirmed(channels, mock_bot):
    result = await channels(
        "discord.pin.add",
        {
            "channel_id": CHANNEL_ID,
            "message_id": MESSAGE_ID,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "pinned"
    assert payload["dry_run"] is False
    mock_bot.pin_message.assert_awaited_once_with(CHANNEL_ID, MESSAGE_ID)


async def test_pin_remove_dry_run_does_not_call_bot(channels, mock_bot):
    result = await channels(
        "discord.pin.remove", {"channel_id": CHANNEL_ID, "message_id": MESSAGE_ID}
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.unpin_message.assert_not_called()


async def test_pin_remove_confirmed(channels, mock_bot):
    result = await channels(
        "discord.pin.remove",
        {
            "channel_id": CHANNEL_ID,
            "message_id": MESSAGE_ID,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "unpinned"
    assert payload["dry_run"] is False
    mock_bot.unpin_message.assert_awaited_once_with(CHANNEL_ID, MESSAGE_ID)


# --- Reactions (via MessageService) ---


async def test_reaction_list(reactions, mock_bot):
    mock_bot.list_reactions.return_value = [{"id": USER_ID, "username": "someone"}]
    result = await reactions(
        "discord.reaction.list",
        {"channel_id": CHANNEL_ID, "message_id": MESSAGE_ID, "emoji": EMOJI, "limit": 50},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload[0]["id"] == USER_ID
    mock_bot.list_reactions.assert_awaited_once_with(CHANNEL_ID, MESSAGE_ID, EMOJI, limit=50)


async def test_reaction_remove_user_dry_run_does_not_call_bot(reactions, mock_bot, audit):
    result = await reactions(
        "discord.reaction.remove_user",
        {
            "channel_id": CHANNEL_ID,
            "message_id": MESSAGE_ID,
            "emoji": EMOJI,
            "user_id": USER_ID,
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.remove_user_reaction.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.reaction.remove_user"


async def test_reaction_remove_user_without_confirmation_rejected(reactions, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await reactions(
            "discord.reaction.remove_user",
            {
                "channel_id": CHANNEL_ID,
                "message_id": MESSAGE_ID,
                "emoji": EMOJI,
                "user_id": USER_ID,
                "dry_run": False,
            },
        )
    mock_bot.remove_user_reaction.assert_not_called()


async def test_reaction_remove_user_confirmed(reactions, mock_bot):
    result = await reactions(
        "discord.reaction.remove_user",
        {
            "channel_id": CHANNEL_ID,
            "message_id": MESSAGE_ID,
            "emoji": EMOJI,
            "user_id": USER_ID,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "removed_user_reaction"
    assert payload["dry_run"] is False
    mock_bot.remove_user_reaction.assert_awaited_once_with(CHANNEL_ID, MESSAGE_ID, EMOJI, USER_ID)


async def test_unknown_tool_returns_none(channels, reactions):
    assert await channels("discord.other.tool", {}) is None
    assert await reactions("discord.other.tool", {}) is None


# --- REST client (new endpoints) ---


def _client_with_transport(handler) -> DiscordRestClient:
    client = DiscordRestClient("token")
    client._client = httpx.AsyncClient(
        base_url=DISCORD_API_BASE,
        headers={"Authorization": "Bot token"},
        transport=httpx.MockTransport(handler),
    )
    return client


async def test_rest_list_reactions_encodes_emoji():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=[])

    client = _client_with_transport(transport)
    result = await client.list_reactions(CHANNEL_ID, MESSAGE_ID, EMOJI, limit=25)
    await client.close()
    assert result == []
    assert seen["url"] == (
        f"{DISCORD_API_BASE}/channels/{CHANNEL_ID}/messages/{MESSAGE_ID}"
        f"/reactions/{EMOJI_ENCODED}?limit=25"
    )


async def test_rest_remove_user_reaction_encodes_emoji():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        return httpx.Response(204)

    client = _client_with_transport(transport)
    await client.remove_user_reaction(CHANNEL_ID, MESSAGE_ID, EMOJI, USER_ID)
    await client.close()
    assert seen["method"] == "DELETE"
    assert seen["url"] == (
        f"{DISCORD_API_BASE}/channels/{CHANNEL_ID}/messages/{MESSAGE_ID}"
        f"/reactions/{EMOJI_ENCODED}/{USER_ID}"
    )
