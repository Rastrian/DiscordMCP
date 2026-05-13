# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.db.models import BotConfig
from discord_mcp_platform.security.secrets import hash_token

log = get_logger("bot_configs")


class BotConfigService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save_config(
        self,
        workspace_id: str,
        name: str,
        bot_token: str | None = None,
        config: dict | None = None,
    ) -> dict:
        """Create a new bot configuration, hashing the token if provided."""
        bot_config = BotConfig(
            workspace_id=workspace_id,
            name=name,
            bot_token_hash=hash_token(bot_token) if bot_token else None,
            config=config or {},
        )
        self._session.add(bot_config)
        await self._session.flush()
        log.info("bot_config_saved", config_id=bot_config.id, workspace_id=workspace_id, name=name)
        return {"id": bot_config.id, "workspace_id": workspace_id, "name": name}

    async def get_config(self, config_id: str) -> dict | None:
        """Retrieve a single bot configuration by ID."""
        stmt = select(BotConfig).where(BotConfig.id == config_id)
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            return None
        return {
            "id": config.id,
            "workspace_id": config.workspace_id,
            "name": config.name,
            "config": config.config,
        }

    async def list_configs(self, workspace_id: str) -> list[dict]:
        """List all bot configurations for a workspace."""
        stmt = select(BotConfig).where(BotConfig.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        configs = result.scalars().all()
        return [{"id": c.id, "name": c.name, "workspace_id": c.workspace_id} for c in configs]

    async def delete_config(self, config_id: str) -> bool:
        """Delete a bot configuration by ID. Returns True if found and deleted."""
        stmt = select(BotConfig).where(BotConfig.id == config_id)
        result = await self._session.execute(stmt)
        config = result.scalar_one_or_none()
        if config is None:
            return False
        await self._session.delete(config)
        await self._session.flush()
        log.info("bot_config_deleted", config_id=config_id)
        return True
