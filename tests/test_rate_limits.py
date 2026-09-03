# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import time

import httpx
import pytest

import discord_mcp_platform.discord.rate_limits as rate_limits
from discord_mcp_platform.discord.rate_limits import RateLimitTracker
from discord_mcp_platform.discord.rest_client import DISCORD_API_BASE, DiscordRestClient
from discord_mcp_platform.errors import RateLimitError


# --- Tracker (pure) ---


def test_global_not_limited_by_default():
    tracker = RateLimitTracker()
    assert tracker.is_global_limited() is False


def test_set_global_limits_until_expiry(monkeypatch):
    tracker = RateLimitTracker()
    now = 1000.0
    monkeypatch.setattr(rate_limits.time, "monotonic", lambda: now)

    tracker.set_global(30.0)
    assert tracker.is_global_limited() is True

    now = 1029.9
    assert tracker.is_global_limited() is True

    now = 1030.1
    assert tracker.is_global_limited() is False


def test_global_wait_time_decreases(monkeypatch):
    tracker = RateLimitTracker()
    now = 1000.0
    monkeypatch.setattr(rate_limits.time, "monotonic", lambda: now)

    tracker.set_global(30.0)
    assert tracker.global_wait_time() == pytest.approx(30.0)
    now = 1010.0
    assert tracker.global_wait_time() == pytest.approx(20.0)


def test_bucket_methods_unchanged(monkeypatch):
    tracker = RateLimitTracker()
    now = 1000.0
    monkeypatch.setattr(rate_limits.time, "monotonic", lambda: now)

    tracker.update("GET:/channels/1/messages", remaining=0, reset_at=1010.0)
    assert tracker.is_limited("GET:/channels/1/messages") is True
    assert tracker.wait_time("GET:/channels/1/messages") == pytest.approx(10.0)

    now = 1010.5
    assert tracker.is_limited("GET:/channels/1/messages") is False
    assert tracker.wait_time("GET:/channels/1/messages") == 0.0


# --- Client (httpx.MockTransport) ---


def _client_with_transport(handler) -> DiscordRestClient:
    client = DiscordRestClient("token")
    client._client = httpx.AsyncClient(
        base_url=DISCORD_API_BASE,
        headers={"Authorization": "Bot token"},
        transport=httpx.MockTransport(handler),
    )
    return client


def _message(content: str = "hello") -> dict:
    return {
        "id": "999999999999999999",
        "author": {"id": "1", "username": "user", "global_name": "User"},
        "content": content,
        "timestamp": "2026-01-01T00:00:00Z",
    }


async def test_429_non_global_retries_once_then_succeeds():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, json={"retry_after": 0.05})
        return httpx.Response(200, json=[_message()])

    client = _client_with_transport(handler)
    result = await client.get_messages("123")
    assert len(calls) == 2
    assert result[0]["content"] == "hello"
    await client.close()


async def test_429_retry_after_above_threshold_raises_immediately():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(429, json={"retry_after": 15.0})

    client = _client_with_transport(handler)
    with pytest.raises(RateLimitError) as exc_info:
        await client.get_messages("123")
    assert len(calls) == 1
    assert exc_info.value.retry_after == 15.0
    await client.close()


async def test_second_429_raises_after_single_retry():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(429, json={"retry_after": 0.01})

    client = _client_with_transport(handler)
    with pytest.raises(RateLimitError):
        await client.get_messages("123")
    assert len(calls) == 2
    await client.close()


async def test_429_global_sets_global_limit_and_raises():
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        return httpx.Response(
            429,
            headers={"x-ratelimit-global": "true", "x-ratelimit-reset-after": "1.0"},
            json={"retry_after": 1.0, "global": True},
        )

    client = _client_with_transport(handler)
    with pytest.raises(RateLimitError):
        await client.get_messages("123")
    assert len(calls) == 1
    assert client._rate_limiter.is_global_limited() is True
    await client.close()


async def test_request_waits_while_global_limit_active():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[_message()])

    client = _client_with_transport(handler)
    client._rate_limiter.set_global(0.05)

    started = time.monotonic()
    result = await client.get_messages("123")
    elapsed = time.monotonic() - started

    assert result[0]["content"] == "hello"
    assert elapsed >= 0.04
    await client.close()
