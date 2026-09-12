# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

"""Regression tests: MCP tool handlers must pass guild_id to the service layer
correctly. These lock the fix for handlers that previously passed arguments in
the wrong positional order (guild_id where code/channel_id was expected), which
made check_discord_permission run against the wrong ID."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from discord_mcp_platform.mcp.tools.invites import get_handler as invite_handler
from discord_mcp_platform.security.policy import PermissionService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.invite_service import InviteService

GUILD_ID = "123456789012345678"
CHANNEL_ID = "234567890123456789"
INVITE_CODE = "abc123"


@pytest.fixture
def mock_bot():
    return AsyncMock()


@pytest.fixture
def audit():
    return AsyncMock(spec=AuditService)


@pytest.fixture
def invite_service(mock_bot):
    return InviteService(mock_bot, PermissionService([], []))


@pytest.fixture
def invites(invite_service, audit):
    return invite_handler(invite_service, audit)


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_invite_create_handler_argument_order(mock_check, invites, mock_bot):
    """create_invite(channel_id=..., guild_id=...) must receive each ID in its
    own parameter (the handler used to swap them positionally)."""
    result = await invites(
        "discord.invite.create",
        {"guild_id": GUILD_ID, "channel_id": CHANNEL_ID},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    assert payload["status"] == "validated"
    assert payload["channel_id"] == CHANNEL_ID
    # check_discord_permission must receive the real guild ID, not the channel ID.
    assert mock_check.call_args.args[1] == GUILD_ID


@patch("discord_mcp_platform.services.invite_service.check_discord_permission")
async def test_invite_delete_handler_argument_order(mock_check, invites, mock_bot):
    """delete_invite(code=..., guild_id=...) must receive each value in its own
    parameter (the handler used to swap them positionally)."""
    result = await invites(
        "discord.invite.delete",
        {"guild_id": GUILD_ID, "code": INVITE_CODE, "dry_run": True},
    )
    assert result is not None
    payload = json.loads(result[0].text)
    # dry-run response must echo the invite code, not the guild ID.
    assert payload["code"] == INVITE_CODE
    assert mock_check.call_args.args[1] == GUILD_ID
