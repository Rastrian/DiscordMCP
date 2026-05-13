# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.api.deps import CurrentUser, require_current_user
from discord_mcp_platform.app.lifecycle import get_db_session
from discord_mcp_platform.db.models import AuditEvent

router = APIRouter()


@router.get("/")
async def list_audit_events(
    session: AsyncSession = Depends(get_db_session),
    current: CurrentUser = Depends(require_current_user),
):
    workspace_id = current.workspace_id or "default"
    stmt = (
        select(AuditEvent)
        .where(AuditEvent.workspace_id == workspace_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(100)
    )
    result = await session.execute(stmt)
    events = result.scalars().all()
    return {
        "events": [
            {
                "id": e.id,
                "workspace_id": e.workspace_id,
                "action": e.action,
                "guild_id": e.guild_id,
                "channel_id": e.channel_id,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in events
        ]
    }
