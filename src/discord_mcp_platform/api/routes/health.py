# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from discord_mcp_platform.app.lifecycle import engine
from discord_mcp_platform.app.settings import settings

router = APIRouter()

_redis = None


async def _get_redis():
    global _redis
    if _redis is None:
        import redis.asyncio as aioredis

        _redis = aioredis.from_url(settings.redis_url)
    return _redis


@router.get("/health")
async def health():
    return {"status": "ok", "service": "discord-mcp-platform", "version": "0.1.0"}


@router.get("/health/ready")
async def health_ready():
    checks: dict[str, str] = {}

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    try:
        r = await _get_redis()
        await r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    return {"status": "ok" if all_ok else "degraded", "checks": checks}
