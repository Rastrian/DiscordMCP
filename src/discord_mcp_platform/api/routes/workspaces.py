# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.api.deps import CurrentUser, get_current_user, require_current_user
from discord_mcp_platform.app.lifecycle import get_db_session
from discord_mcp_platform.control_plane.workspaces import WorkspaceService

router = APIRouter()


class CreateWorkspaceRequest(BaseModel):
    name: str
    slug: str


@router.post("/")
async def create_workspace(
    body: CreateWorkspaceRequest,
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser = Depends(require_current_user),
):
    svc = WorkspaceService(session)
    ws = await svc.create_workspace(body.name, body.slug, owner_user_id=current.user_id)
    return ws


@router.get("/")
async def list_workspaces(
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser | None = Depends(get_current_user),
):
    if current is None:
        return {"workspaces": []}
    svc = WorkspaceService(session)
    workspaces = await svc.list_user_workspaces(user_id=current.user_id)
    return {"workspaces": workspaces}


@router.get("/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser | None = Depends(get_current_user),
):
    if current is None:
        return {"error": "not_authenticated"}
    svc = WorkspaceService(session)
    ws = await svc.get_workspace(workspace_id)
    return ws or {"error": "not_found"}
