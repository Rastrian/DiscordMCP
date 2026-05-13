from __future__ import annotations

from mcp.server import Server
from mcp.types import Prompt

from discord_mcp_platform.mcp.prompts.community_summary import (
    get_prompts as community_prompts,
    handle as community_handle,
)
from discord_mcp_platform.mcp.prompts.moderation_review import (
    get_prompts as moderation_prompts,
    handle as moderation_handle,
)
from discord_mcp_platform.mcp.prompts.automation_builder import (
    get_prompts as automation_prompts,
    handle as automation_handle,
)
from discord_mcp_platform.mcp.prompts.incident_report import (
    get_prompts as incident_prompts,
    handle as incident_handle,
)
from discord_mcp_platform.mcp.prompts.support_triage import (
    get_prompts as support_prompts,
    handle as support_handle,
)


def register_all_prompts(server: Server) -> None:
    prompt_defs: list[Prompt] = [
        *community_prompts(),
        *moderation_prompts(),
        *automation_prompts(),
        *incident_prompts(),
        *support_prompts(),
    ]

    handlers = [
        community_handle,
        moderation_handle,
        automation_handle,
        incident_handle,
        support_handle,
    ]

    @server.list_prompts()
    async def _list_prompts():
        return prompt_defs

    @server.get_prompt()
    async def _get_prompt(name: str, arguments: dict | None = None):
        for handler in handlers:
            result = await handler(name, arguments)
            if result is not None:
                return result
        raise ValueError(f"unknown prompt: {name}")
