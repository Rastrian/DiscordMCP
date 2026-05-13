# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.db.models import Workspace


def _workspace_to_dict(ws: Workspace) -> dict:
    return {
        "id": ws.id,
        "name": ws.name,
        "slug": ws.slug,
        "owner_user_id": ws.owner_user_id,
        "created_at": ws.created_at.isoformat() if ws.created_at else None,
    }


class WorkspaceService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_workspace(self, name: str, slug: str, owner_user_id: str) -> dict:
        ws = Workspace(name=name, slug=slug, owner_user_id=owner_user_id)
        self._session.add(ws)
        await self._session.flush()
        return _workspace_to_dict(ws)

    async def get_workspace(self, workspace_id: str) -> dict | None:
        stmt = select(Workspace).where(Workspace.id == workspace_id)
        result = await self._session.execute(stmt)
        ws = result.scalar_one_or_none()
        if ws is None:
            return None
        return _workspace_to_dict(ws)

    async def list_user_workspaces(self, user_id: str) -> list[dict]:
        stmt = select(Workspace).where(Workspace.owner_user_id == user_id)
        result = await self._session.execute(stmt)
        workspaces = result.scalars().all()
        return [_workspace_to_dict(ws) for ws in workspaces]
