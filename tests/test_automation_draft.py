# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.models import AutomationDraftInput
from discord_mcp_platform.services.automation_service import AutomationService


async def test_automation_draft_schema():
    input_data = AutomationDraftInput(
        guild_id="123456789012345678",
        description="Answer FAQs and escalate unresolved questions.",
        target_channel_ids=["234567890123456789"],
    )
    svc = AutomationService(session=None)
    result = await svc.draft(input_data)
    assert result.status == "drafted"
    assert result.draft_id is not None
    assert "FAQ" in result.summary or "123456789012345678" in result.summary
