# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import discord_mcp_platform.api.routes.health as health_module
from discord_mcp_platform.api.routes.health import router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class _FailingConnect:
    async def __aenter__(self):
        raise RuntimeError("secret-db-detail")

    async def __aexit__(self, *args) -> bool:
        return False


class _FailingEngine:
    def connect(self) -> _FailingConnect:
        return _FailingConnect()


async def _failing_get_redis():
    raise RuntimeError("secret-redis-detail")


def test_health_liveness():
    response = _client().get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health_ready_degraded_does_not_leak_error_details(monkeypatch):
    monkeypatch.setattr(health_module, "engine", _FailingEngine())
    monkeypatch.setattr(health_module, "_get_redis", _failing_get_redis)
    monkeypatch.setattr(health_module, "log", MagicMock())

    response = _client().get("/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "error"
    assert body["checks"]["redis"] == "error"
    assert "secret-db-detail" not in response.text
    assert "secret-redis-detail" not in response.text


def test_health_ready_logs_error_details(monkeypatch):
    monkeypatch.setattr(health_module, "engine", _FailingEngine())
    monkeypatch.setattr(health_module, "_get_redis", _failing_get_redis)
    mock_log = MagicMock()
    monkeypatch.setattr(health_module, "log", mock_log)

    _client().get("/health/ready")

    mock_log.warning.assert_any_call("health_database_error", error="secret-db-detail")
    mock_log.warning.assert_any_call("health_redis_error", error="secret-redis-detail")
