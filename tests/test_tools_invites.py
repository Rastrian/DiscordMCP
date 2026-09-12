# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import ValidationError

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.discord.models import (
    InviteTargetAddInput,
    InviteTargetBulkAddInput,
    InviteTargetBulkRemoveInput,
    InviteTargetRemoveInput,
)
from discord_mcp_platform.discord.rest_client import DISCORD_API_BASE, DiscordRestClient
from discord_mcp_platform.errors import PolicyDeniedError
from discord_mcp_platform.mcp.tools.invites import get_handler as invite_handler
from discord_mcp_platform.mcp.tools.invites import get_tools as invite_tools
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.invite_service import InviteService

GUILD_ID = "123456789012345678"
USER_1 = "111111111111111111"
USER_2 = "222222222222222222"
INVITE_CODE = "abc123"
SNOWFLAKE = "123456789012345678"


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
def invite_service(mock_bot, permissions):
    return InviteService(mock_bot, permissions)


@pytest.fixture
def invites(invite_service, audit):
    return invite_handler(invite_service, audit)


def test_invite_target_tool_names():
    names = {tool.name for tool in invite_tools()}
    assert {
        "discord.invite.target.add",
        "discord.invite.target.remove",
        "discord.invite.target.bulk_add",
        "discord.invite.target.bulk_remove",
    } <= names


# --- discord.invite.target.add / remove (via InviteService) ---


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_target_add_dry_run_does_not_call_bot(mock_check, invites, mock_bot, audit):
    result = await invites(
        "discord.invite.target.add",
        {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_id": USER_1},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    assert payload["user_id"] == USER_1
    mock_bot.add_invite_target_user.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.invite.target.add"
    assert audit.record.call_args.kwargs["guild_id"] == GUILD_ID
    assert audit.record.call_args.kwargs["target_id"] == INVITE_CODE


async def test_target_add_without_confirmation_rejected(invites, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invites(
            "discord.invite.target.add",
            {
                "guild_id": GUILD_ID,
                "code": INVITE_CODE,
                "user_id": USER_1,
                "dry_run": False,
            },
        )
    mock_bot.add_invite_target_user.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_target_add_confirmed(mock_check, invites, mock_bot):
    result = await invites(
        "discord.invite.target.add",
        {
            "guild_id": GUILD_ID,
            "code": INVITE_CODE,
            "user_id": USER_1,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "added"
    assert payload["dry_run"] is False
    mock_bot.add_invite_target_user.assert_awaited_once_with(INVITE_CODE, USER_1)


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_target_remove_dry_run_does_not_call_bot(mock_check, invites, mock_bot, audit):
    result = await invites(
        "discord.invite.target.remove",
        {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_id": USER_1},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.remove_invite_target_user.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.invite.target.remove"


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_target_remove_confirmed(mock_check, invites, mock_bot):
    result = await invites(
        "discord.invite.target.remove",
        {
            "guild_id": GUILD_ID,
            "code": INVITE_CODE,
            "user_id": USER_1,
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "removed"
    assert payload["dry_run"] is False
    mock_bot.remove_invite_target_user.assert_awaited_once_with(INVITE_CODE, USER_1)


async def test_target_remove_without_confirmation_rejected(invites, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invites(
            "discord.invite.target.remove",
            {
                "guild_id": GUILD_ID,
                "code": INVITE_CODE,
                "user_id": USER_1,
                "dry_run": False,
            },
        )
    mock_bot.remove_invite_target_user.assert_not_called()


# --- discord.invite.target.bulk_add / bulk_remove (via InviteService) ---


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_add_dry_run_does_not_call_bot(mock_check, invites, mock_bot, audit):
    result = await invites(
        "discord.invite.target.bulk_add",
        {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": [USER_1, USER_2]},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    assert payload["count"] == 2
    mock_bot.bulk_add_invite_target_users.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.invite.target.bulk_add"
    assert audit.record.call_args.kwargs["details"]["user_ids"] == [USER_1, USER_2]


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_add_confirmed(mock_check, invites, mock_bot):
    result = await invites(
        "discord.invite.target.bulk_add",
        {
            "guild_id": GUILD_ID,
            "code": INVITE_CODE,
            "user_ids": [USER_1, USER_2],
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "bulk_added"
    assert payload["dry_run"] is False
    assert payload["count"] == 2
    mock_bot.bulk_add_invite_target_users.assert_awaited_once_with(INVITE_CODE, [USER_1, USER_2])


async def test_bulk_add_without_confirmation_rejected(invites, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invites(
            "discord.invite.target.bulk_add",
            {
                "guild_id": GUILD_ID,
                "code": INVITE_CODE,
                "user_ids": [USER_1],
                "dry_run": False,
            },
        )
    mock_bot.bulk_add_invite_target_users.assert_not_called()


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_remove_dry_run_does_not_call_bot(mock_check, invites, mock_bot, audit):
    result = await invites(
        "discord.invite.target.bulk_remove",
        {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": [USER_1, USER_2]},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["dry_run"] is True
    mock_bot.bulk_remove_invite_target_users.assert_not_called()
    audit.record.assert_awaited_once()
    assert audit.record.call_args.kwargs["action"] == "discord.invite.target.bulk_remove"


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_bulk_remove_confirmed(mock_check, invites, mock_bot):
    result = await invites(
        "discord.invite.target.bulk_remove",
        {
            "guild_id": GUILD_ID,
            "code": INVITE_CODE,
            "user_ids": [USER_1, USER_2],
            "dry_run": False,
            "confirmation": "yes",
        },
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "bulk_removed"
    assert payload["dry_run"] is False
    mock_bot.bulk_remove_invite_target_users.assert_awaited_once_with(INVITE_CODE, [USER_1, USER_2])


async def test_bulk_remove_without_confirmation_rejected(invites, mock_bot):
    with pytest.raises(PolicyDeniedError):
        await invites(
            "discord.invite.target.bulk_remove",
            {
                "guild_id": GUILD_ID,
                "code": INVITE_CODE,
                "user_ids": [USER_1],
                "dry_run": False,
            },
        )
    mock_bot.bulk_remove_invite_target_users.assert_not_called()


# --- Input validation (pydantic models) ---


def test_target_add_rejects_non_snowflake_user_id():
    with pytest.raises(ValidationError):
        InviteTargetAddInput.model_validate(
            {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_id": "not-a-snowflake"}
        )


def test_target_add_rejects_non_snowflake_guild_id():
    with pytest.raises(ValidationError):
        InviteTargetAddInput.model_validate(
            {"guild_id": "123", "code": INVITE_CODE, "user_id": USER_1}
        )


def test_target_remove_rejects_non_snowflake_user_id():
    with pytest.raises(ValidationError):
        InviteTargetRemoveInput.model_validate(
            {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_id": "12345"}
        )


def test_bulk_add_rejects_empty_user_ids():
    with pytest.raises(ValidationError):
        InviteTargetBulkAddInput.model_validate(
            {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": []}
        )


def test_bulk_add_rejects_more_than_1000_user_ids():
    with pytest.raises(ValidationError):
        InviteTargetBulkAddInput.model_validate(
            {
                "guild_id": GUILD_ID,
                "code": INVITE_CODE,
                "user_ids": [SNOWFLAKE] * 1001,
            }
        )


def test_bulk_add_accepts_exactly_1000_user_ids():
    data = InviteTargetBulkAddInput.model_validate(
        {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": [SNOWFLAKE] * 1000}
    )
    assert len(data.user_ids) == 1000


def test_bulk_add_rejects_non_snowflake_item_in_user_ids():
    with pytest.raises(ValidationError):
        InviteTargetBulkAddInput.model_validate(
            {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": [USER_1, "bad"]}
        )


def test_bulk_remove_rejects_empty_user_ids():
    with pytest.raises(ValidationError):
        InviteTargetBulkRemoveInput.model_validate(
            {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": []}
        )


def test_bulk_remove_rejects_more_than_1000_user_ids():
    with pytest.raises(ValidationError):
        InviteTargetBulkRemoveInput.model_validate(
            {
                "guild_id": GUILD_ID,
                "code": INVITE_CODE,
                "user_ids": [SNOWFLAKE] * 1001,
            }
        )


def test_bulk_remove_rejects_non_snowflake_item_in_user_ids():
    with pytest.raises(ValidationError):
        InviteTargetBulkRemoveInput.model_validate(
            {"guild_id": GUILD_ID, "code": INVITE_CODE, "user_ids": ["oops", USER_1]}
        )


async def test_unknown_tool_returns_none(invites):
    assert await invites("discord.other.tool", {}) is None


# --- REST client (invite target-users endpoints) ---


def _client_with_transport(handler) -> DiscordRestClient:
    client = DiscordRestClient("token")
    client._client = httpx.AsyncClient(
        base_url=DISCORD_API_BASE,
        headers={"Authorization": "Bot token"},
        transport=httpx.MockTransport(handler),
    )
    return client


async def test_rest_add_invite_target_user_builds_url():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        return httpx.Response(204)

    client = _client_with_transport(transport)
    await client.add_invite_target_user(INVITE_CODE, USER_1)
    await client.close()
    assert seen["method"] == "PUT"
    assert seen["url"] == f"{DISCORD_API_BASE}/invites/{INVITE_CODE}/target-users/{USER_1}"


async def test_rest_remove_invite_target_user_builds_url():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        return httpx.Response(204)

    client = _client_with_transport(transport)
    await client.remove_invite_target_user(INVITE_CODE, USER_1)
    await client.close()
    assert seen["method"] == "DELETE"
    assert seen["url"] == f"{DISCORD_API_BASE}/invites/{INVITE_CODE}/target-users/{USER_1}"


async def test_rest_bulk_add_invite_target_users_sends_body():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["json"] = json.loads(request.content)
        return httpx.Response(204)

    client = _client_with_transport(transport)
    await client.bulk_add_invite_target_users(INVITE_CODE, [USER_1, USER_2])
    await client.close()
    assert seen["method"] == "POST"
    assert seen["url"] == f"{DISCORD_API_BASE}/invites/{INVITE_CODE}/target-users/bulk-add"
    assert seen["json"] == {"user_ids": [USER_1, USER_2]}


async def test_rest_bulk_remove_invite_target_users_sends_body():
    seen: dict = {}

    def transport(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["url"] = str(request.url)
        seen["json"] = json.loads(request.content)
        return httpx.Response(204)

    client = _client_with_transport(transport)
    await client.bulk_remove_invite_target_users(INVITE_CODE, [USER_2])
    await client.close()
    assert seen["method"] == "POST"
    assert seen["url"] == f"{DISCORD_API_BASE}/invites/{INVITE_CODE}/target-users/bulk-delete"
    assert seen["json"] == {"user_ids": [USER_2]}
