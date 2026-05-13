# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.models import AutomationDraftInput, AutomationDraftOutput

log = get_logger("automation_service")


class AutomationService:
    def __init__(self, session=None, session_factory=None) -> None:
        self._session = session
        self._session_factory = session_factory

    async def _with_session(self, fn):
        if self._session is not None:
            return await fn(self._session)
        if self._session_factory is not None:
            async with self._session_factory() as session:
                return await fn(session)
        return None

    async def draft(self, input_data: AutomationDraftInput) -> AutomationDraftOutput:
        draft_id = str(uuid.uuid4())
        summary = (
            f"Automation draft for guild {input_data.guild_id}: {input_data.description[:200]}"
        )

        async def _write(session):
            from discord_mcp_platform.db.models import Automation

            record = Automation(
                id=draft_id,
                workspace_id=input_data.workspace_id,
                guild_id=input_data.guild_id,
                name="draft",
                description=input_data.description,
                trigger_type="manual",
                action_type="draft",
                target_channel_ids=str(input_data.target_channel_ids),
                status="draft",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(record)
            await session.flush()

        await self._with_session(_write)

        log.info("automation_draft", draft_id=draft_id, guild_id=input_data.guild_id)
        return AutomationDraftOutput(status="drafted", draft_id=draft_id, summary=summary)
