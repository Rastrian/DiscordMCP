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
from discord_mcp_platform.app.bot_state import get_bot
from discord_mcp_platform.control_plane.installations import InstallationService

router = APIRouter()


class InstallBotRequest(BaseModel):
    workspace_id: str
    guild_id: str


@router.get("/")
async def list_bots(
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser | None = Depends(get_current_user),
):
    workspace_id = current.workspace_id or "default" if current else "default"
    svc = InstallationService(session)
    installations = await svc.list_installations(workspace_id=workspace_id)
    bot = get_bot()
    bot_info = None
    if bot and bot.bot_id:
        bot_info = {"bot_id": bot.bot_id}
    return {"bots": installations, "bot": bot_info}


@router.get("/invite")
async def get_invite_url(guild_id: str | None = None):
    bot = get_bot()
    if bot is None:
        return {"error": "bot_not_configured"}
    permissions = (
        0x00000A28  # MANAGE_CHANNELS + SEND_MESSAGES + READ_MESSAGE_HISTORY + VIEW_CHANNEL
    )
    url = bot.get_invite_url(permissions=permissions, guild_id=guild_id)
    return {"invite_url": url}


@router.post("/")
async def install_bot(
    body: InstallBotRequest,
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser = Depends(require_current_user),
):
    svc = InstallationService(session)
    result = await svc.install_guild(
        workspace_id=body.workspace_id,
        guild_id=body.guild_id,
        installed_by_user_id=current.user_id,
    )
    return result
