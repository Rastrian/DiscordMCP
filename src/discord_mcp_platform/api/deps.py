# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.app.lifecycle import get_db_session
from discord_mcp_platform.db.models import WorkspaceMembership


@dataclass
class CurrentUser:
    user_id: str
    discord_user_id: str
    username: str
    workspace_id: str | None = None


async def get_current_user(
    request: Request, session: AsyncSession = Depends(get_db_session)
) -> CurrentUser | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    discord_user_id = request.session.get("discord_user_id", "")
    username = request.session.get("username", "")

    # Find user's workspace
    stmt = select(WorkspaceMembership).where(WorkspaceMembership.user_id == user_id)
    result = await session.execute(stmt)
    membership = result.scalar_one_or_none()
    workspace_id = membership.workspace_id if membership else None

    return CurrentUser(
        user_id=user_id,
        discord_user_id=discord_user_id,
        username=username,
        workspace_id=workspace_id,
    )


async def require_current_user(
    current: CurrentUser | None = Depends(get_current_user),
) -> CurrentUser:
    if current is None:
        from discord_mcp_platform.errors import AuthenticationError

        raise AuthenticationError("not authenticated")
    return current
