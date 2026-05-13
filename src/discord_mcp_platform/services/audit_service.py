# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from datetime import datetime, timezone

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.security.redaction import redact_dict

log = get_logger("audit_service")


class AuditService:
    def __init__(self, session=None, session_factory=None) -> None:
        self._session = session
        self._session_factory = session_factory

    async def list_events(
        self,
        *,
        workspace_id: str,
        guild_id: str | None = None,
        action: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        from sqlalchemy import select
        from discord_mcp_platform.db.models import AuditEvent

        async def _query(session):
            stmt = select(AuditEvent).where(AuditEvent.workspace_id == workspace_id)
            if guild_id:
                stmt = stmt.where(AuditEvent.guild_id == guild_id)
            if action:
                stmt = stmt.where(AuditEvent.action == action)
            stmt = stmt.order_by(AuditEvent.created_at.desc()).limit(limit)
            result = await session.execute(stmt)
            return result.scalars().all()

        events = await self._with_session(_query)
        if events is None:
            return []
        return [
            {
                "id": e.id,
                "action": e.action,
                "guild_id": e.guild_id,
                "channel_id": e.channel_id,
                "target_id": e.target_id,
                "details": e.details,
                "created_at": str(e.created_at),
            }
            for e in events
        ]

    async def record(
        self,
        *,
        workspace_id: str,
        user_id: str | None = None,
        mcp_client_id: str | None = None,
        action: str,
        guild_id: str | None = None,
        channel_id: str | None = None,
        target_id: str | None = None,
        details: dict | None = None,
    ) -> None:
        safe_details = redact_dict(details) if details else None

        async def _write(session):
            from discord_mcp_platform.db.models import AuditEvent

            event = AuditEvent(
                workspace_id=workspace_id,
                user_id=user_id,
                mcp_client_id=mcp_client_id,
                action=action,
                guild_id=guild_id,
                channel_id=channel_id,
                target_id=target_id,
                details=str(safe_details),
                created_at=datetime.now(timezone.utc),
            )
            session.add(event)
            await session.flush()

        await self._with_session(_write)

        log.info(
            "audit",
            action=action,
            workspace_id=workspace_id,
            guild_id=guild_id,
            channel_id=channel_id,
            target_id=target_id,
        )

    async def _with_session(self, fn):
        if self._session is not None:
            return await fn(self._session)
        if self._session_factory is not None:
            async with self._session_factory() as session:
                return await fn(session)
        return None
