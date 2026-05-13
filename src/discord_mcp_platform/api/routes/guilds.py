# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.api.deps import CurrentUser, get_current_user
from discord_mcp_platform.app.lifecycle import get_db_session
from discord_mcp_platform.control_plane.installations import InstallationService

router = APIRouter()


@router.get("/")
async def list_guilds(
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser | None = Depends(get_current_user),
):
    workspace_id = current.workspace_id or "default" if current else "default"
    svc = InstallationService(session)
    installations = await svc.list_installations(workspace_id=workspace_id)
    return {"guilds": installations}


@router.get("/{guild_id}")
async def get_guild(
    guild_id: str,
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser | None = Depends(get_current_user),
):
    workspace_id = current.workspace_id or "default" if current else "default"
    svc = InstallationService(session)
    installation = await svc.get_installation(workspace_id=workspace_id, guild_id=guild_id)
    return installation or {"guild_id": guild_id, "installed": False}
