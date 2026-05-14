# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.security.allowlist import Allowlist
from discord_mcp_platform.services.agent_service import AgentService


@pytest.fixture
def mock_bot():
    bot = AsyncMock(spec=BotRuntime)
    bot.bot_id = "111111111111111111"
    return bot


@pytest.fixture
def allowlist():
    return Allowlist(guild_ids=["222222222222222222"], channel_ids=["333333333333333333"])


@pytest.fixture
def agent(mock_bot, allowlist):
    return AgentService(
        bot=mock_bot,
        allowlist=allowlist,
        api_base_url="https://api.example.com",
        api_key="test-key",
        model="test-model",
        system_prompt="You are a test bot.",
        max_history=10,
        cooldown_seconds=1,
    )


def _make_message(
    content: str,
    author_id: str = "444444444444444444",
    channel_id: str = "333333333333333333",
    guild_id: str = "222222222222222222",
) -> dict:
    return {
        "event_type": "MESSAGE_CREATE",
        "content": content,
        "channel_id": channel_id,
        "guild_id": guild_id,
        "author": {
            "id": author_id,
            "username": "testuser",
            "global_name": "Test User",
            "bot": False,
        },
        "id": "555555555555555555",
    }


# --- Mention detection ---


def test_is_mentioned_with_standard_mention(agent):
    event = _make_message("<@111111111111111111> hello")
    assert agent.is_mentioned(event) is True


def test_is_mentioned_with_nickname_mention(agent):
    event = _make_message("<@!111111111111111111> hello")
    assert agent.is_mentioned(event) is True


def test_is_not_mentioned(agent):
    event = _make_message("just saying hello")
    assert agent.is_mentioned(event) is False


# --- Allowlist ---


async def test_is_allowed_in_allowed_guild_channel(agent):
    event = _make_message("hi", guild_id="222222222222222222", channel_id="333333333333333333")
    assert await agent.is_allowed(event) is True


async def test_is_not_allowed_in_disallowed_guild(agent):
    event = _make_message("hi", guild_id="999999999999999999")
    assert await agent.is_allowed(event) is False


async def test_is_not_allowed_in_disallowed_channel(agent):
    event = _make_message("hi", channel_id="999999999999999999")
    assert await agent.is_allowed(event) is False


# --- Cooldown ---


def test_cooldown_allows_first_request(agent):
    assert agent._check_cooldown("user1") is True


def test_cooldown_blocks_rapid_request(agent):
    agent._mark_cooldown("user1")
    assert agent._check_cooldown("user1") is False


# --- Ignore bot messages ---


async def test_ignores_own_message(agent, mock_bot):
    event = _make_message("<@111111111111111111> hello", author_id="111111111111111111")
    await agent.handle_message(event)
    mock_bot.send_message.assert_not_called()


async def test_ignores_other_bot_message(agent, mock_bot):
    event = _make_message("<@111111111111111111> hello")
    event["author"]["bot"] = True
    await agent.handle_message(event)
    mock_bot.send_message.assert_not_called()


# --- Full flow ---


async def test_handle_message_responds(agent, mock_bot):
    event = _make_message("<@111111111111111111> What is 2+2?")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": "2+2 equals 4!"}],
        "stop_reason": "end_turn",
    }

    mock_bot.send_message.return_value = MagicMock(id="msg_123")

    with patch.object(agent, "_get_http_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_factory.return_value = mock_client

        await agent.handle_message(event)

    # Sends "Thinking..." then edits with the actual response
    mock_bot.send_message.assert_called_once_with("333333333333333333", "Thinking...")
    mock_bot.edit_message.assert_called_once_with("333333333333333333", "msg_123", "2+2 equals 4!")
    mock_bot.add_reaction.assert_any_call("333333333333333333", "555555555555555555", "✅")


async def test_handle_message_no_mention_ignored(agent, mock_bot):
    event = _make_message("What is 2+2?")
    await agent.handle_message(event)
    mock_bot.send_message.assert_not_called()


async def test_handle_message_llm_error_no_crash(agent, mock_bot):
    event = _make_message("<@111111111111111111> hello")

    mock_bot.send_message.return_value = MagicMock(id="msg_placeholder")

    with patch.object(agent, "_get_http_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=MagicMock(status_code=500, text="error"))
        mock_client_factory.return_value = mock_client

        await agent.handle_message(event)

    # On error: placeholder is deleted, ❌ reaction added
    mock_bot.delete_message.assert_called_once_with("333333333333333333", "msg_placeholder")
    mock_bot.add_reaction.assert_any_call("333333333333333333", "555555555555555555", "❌")


async def test_handle_message_truncates_long_response(agent, mock_bot):
    event = _make_message("<@111111111111111111> tell me a story")

    long_text = "x" * 3000
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": long_text}],
        "stop_reason": "end_turn",
    }

    mock_bot.send_message.return_value = MagicMock(id="msg_123")

    with patch.object(agent, "_get_http_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_factory.return_value = mock_client

        await agent.handle_message(event)

    edited_content = mock_bot.edit_message.call_args[0][2]
    assert len(edited_content) <= 2000


async def test_history_is_maintained(agent, mock_bot):
    event = _make_message("<@111111111111111111> hello")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": "Hi there!"}],
        "stop_reason": "end_turn",
    }

    with patch.object(agent, "_get_http_client") as mock_client_factory:
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_factory.return_value = mock_client

        await agent.handle_message(event)

    history = agent._get_history("333333333333333333")
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
