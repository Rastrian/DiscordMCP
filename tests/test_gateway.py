# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio

from websockets.exceptions import ConnectionClosed
from websockets.frames import Close

import discord_mcp_platform.discord.gateway as gateway_module
from discord_mcp_platform.discord.gateway import DiscordGateway, _backoff_delay


# --- _backoff_delay (pure) ---


def test_backoff_delay_grows_and_caps_at_60(monkeypatch):
    monkeypatch.setattr(gateway_module.random, "uniform", lambda a, b: 0.0)
    delays = [_backoff_delay(attempt) for attempt in range(8)]
    assert delays == [1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0, 60.0]


def test_backoff_delay_bounds_with_jitter():
    for attempt in range(12):
        delay = _backoff_delay(attempt)
        assert 1.0 <= delay <= 61.0


# --- session_start_limit on first connect ---


class FakeRest:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls = 0

    async def get_gateway_bot(self) -> dict:
        self.calls += 1
        return self.payload


class _FailingConnect:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    async def __aenter__(self):
        raise self._exc

    async def __aexit__(self, *args) -> bool:
        return False


class _EmptyWs:
    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


class _OkConnect:
    def __init__(self, ws: _EmptyWs) -> None:
        self._ws = ws

    async def __aenter__(self) -> _EmptyWs:
        return self._ws

    async def __aexit__(self, *args) -> bool:
        return False


async def test_session_start_remaining_zero_stops_without_connect(monkeypatch):
    fake_rest = FakeRest({"session_start_limit": {"remaining": 0, "total": 1000}})
    ws_attempts: list[str] = []

    def fake_ws_connect(url):
        ws_attempts.append(url)
        return _FailingConnect(ConnectionClosed(Close(1000, "x"), None))

    monkeypatch.setattr("websockets.asyncio.client.connect", fake_ws_connect)

    gateway = DiscordGateway("token", rest=fake_rest)
    await asyncio.wait_for(gateway.connect(), timeout=1.0)

    assert fake_rest.calls == 1
    assert ws_attempts == []  # never attempted to open a websocket
    assert gateway._running is False


async def test_session_start_remaining_positive_proceeds_to_connect(monkeypatch):
    fake_rest = FakeRest({"session_start_limit": {"remaining": 5, "total": 1000}})
    ws_attempts: list[str] = []
    gateway = DiscordGateway("token", rest=fake_rest)

    def fake_ws_connect(url):
        ws_attempts.append(url)
        return _FailingConnect(RuntimeError("dns failure"))

    async def fake_sleep(delay: float) -> None:
        gateway._running = False  # stop the reconnect loop after the first backoff

    monkeypatch.setattr("websockets.asyncio.client.connect", fake_ws_connect)
    monkeypatch.setattr(gateway_module.asyncio, "sleep", fake_sleep)

    await asyncio.wait_for(gateway.connect(), timeout=1.0)

    assert fake_rest.calls == 1
    assert len(ws_attempts) == 1
    assert gateway._running is False


async def test_no_rest_client_skips_session_start_check(monkeypatch):
    ws_attempts: list[str] = []
    gateway = DiscordGateway("token")

    def fake_ws_connect(url):
        ws_attempts.append(url)
        return _FailingConnect(RuntimeError("boom"))

    async def fake_sleep(delay: float) -> None:
        gateway._running = False

    monkeypatch.setattr("websockets.asyncio.client.connect", fake_ws_connect)
    monkeypatch.setattr(gateway_module.asyncio, "sleep", fake_sleep)

    await asyncio.wait_for(gateway.connect(), timeout=1.0)
    assert len(ws_attempts) == 1


# --- reconnect backoff uses _backoff_delay and resets on success ---


async def test_reconnect_backoff_is_exponential(monkeypatch):
    monkeypatch.setattr(gateway_module.random, "uniform", lambda a, b: 0.0)
    gateway = DiscordGateway("token")
    delays: list[float] = []

    def fake_ws_connect(url):
        return _FailingConnect(ConnectionClosed(Close(1000, "closed"), None))

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)
        if len(delays) >= 3:
            gateway._running = False

    monkeypatch.setattr("websockets.asyncio.client.connect", fake_ws_connect)
    monkeypatch.setattr(gateway_module.asyncio, "sleep", fake_sleep)

    await asyncio.wait_for(gateway.connect(), timeout=1.0)
    assert delays == [1.0, 2.0, 4.0]


async def test_backoff_counter_resets_after_successful_connection(monkeypatch):
    monkeypatch.setattr(gateway_module.random, "uniform", lambda a, b: 0.0)
    gateway = DiscordGateway("token")
    delays: list[float] = []
    connect_calls = {"n": 0}

    def fake_ws_connect(url):
        connect_calls["n"] += 1
        if connect_calls["n"] in (1, 3):
            return _FailingConnect(ConnectionClosed(Close(1000, "flaky"), None))
        return _OkConnect(_EmptyWs())  # connect succeeds; receive loop yields nothing

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)
        if len(delays) >= 2:
            gateway._running = False

    monkeypatch.setattr("websockets.asyncio.client.connect", fake_ws_connect)
    monkeypatch.setattr(gateway_module.asyncio, "sleep", fake_sleep)

    await asyncio.wait_for(gateway.connect(), timeout=1.0)
    # First failure: attempt 0 -> 1.0; successful connect resets counter; next failure: attempt 0 -> 1.0
    assert delays == [1.0, 1.0]
