# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.db.models import GuildInstallation


def _installation_to_dict(inst: GuildInstallation) -> dict:
    return {
        "id": inst.id,
        "workspace_id": inst.workspace_id,
        "guild_id": inst.guild_id,
        "installed_by_user_id": inst.installed_by_user_id,
        "active": inst.active,
        "created_at": inst.created_at.isoformat() if inst.created_at else None,
    }


class InstallationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def install_guild(
        self,
        workspace_id: str,
        guild_id: str,
        installed_by_user_id: str,
    ) -> dict:
        inst = GuildInstallation(
            workspace_id=workspace_id,
            guild_id=guild_id,
            installed_by_user_id=installed_by_user_id,
        )
        self._session.add(inst)
        await self._session.flush()
        return _installation_to_dict(inst)

    async def get_installation(self, workspace_id: str, guild_id: str) -> dict | None:
        stmt = select(GuildInstallation).where(
            GuildInstallation.workspace_id == workspace_id,
            GuildInstallation.guild_id == guild_id,
            GuildInstallation.active.is_(True),
        )
        result = await self._session.execute(stmt)
        inst = result.scalar_one_or_none()
        if inst is None:
            return None
        return _installation_to_dict(inst)

    async def list_installations(self, workspace_id: str) -> list[dict]:
        stmt = select(GuildInstallation).where(
            GuildInstallation.workspace_id == workspace_id,
            GuildInstallation.active.is_(True),
        )
        result = await self._session.execute(stmt)
        installations = result.scalars().all()
        return [_installation_to_dict(inst) for inst in installations]
