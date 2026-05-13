# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.api.deps import CurrentUser, get_current_user, require_current_user
from discord_mcp_platform.app.lifecycle import get_db_session
from discord_mcp_platform.services.automation_service import AutomationService

router = APIRouter()


class CreateAutomationRequest(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    description: str = Field(min_length=1, max_length=2000)
    target_channel_ids: list[str] = Field(default_factory=list)


@router.get("/")
async def list_automations(
    current: CurrentUser | None = Depends(get_current_user),
):
    workspace_id = current.workspace_id or "default" if current else "default"
    return {"automations": [], "workspace_id": workspace_id}


@router.post("/")
async def create_automation(
    body: CreateAutomationRequest,
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser = Depends(require_current_user),
):
    from discord_mcp_platform.discord.models import AutomationDraftInput

    workspace_id = current.workspace_id or "default"
    svc = AutomationService(session)
    input_data = AutomationDraftInput(
        guild_id=body.guild_id,
        description=body.description,
        target_channel_ids=body.target_channel_ids,
        workspace_id=workspace_id,
    )
    result = await svc.draft(input_data)
    return result.model_dump()
