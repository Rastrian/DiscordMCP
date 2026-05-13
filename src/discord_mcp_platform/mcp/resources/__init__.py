from __future__ import annotations

import json
import re
from typing import Any

from mcp.server import Server
from mcp.types import Resource

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.mcp.resources.guild import get_resources as guild_resources
from discord_mcp_platform.mcp.resources.channel import get_resources as channel_resources
from discord_mcp_platform.mcp.resources.message import get_resources as message_resources
from discord_mcp_platform.mcp.resources.automation import get_resources as automation_resources

log = get_logger("mcp_resources")

# ---------------------------------------------------------------------------
# URI routing
# ---------------------------------------------------------------------------

# Patterns for the supported resource URIs.
_GUILDS_RE = re.compile(r"^discord://guilds$")
_CHANNELS_RE = re.compile(r"^discord://channels/(?P<guild_id>\d+)$")
_MESSAGES_RE = re.compile(r"^discord://messages/(?P<channel_id>\d+)$")
_AUTOMATIONS_RE = re.compile(r"^discord://automations/(?P<guild_id>\d+)$")


def _model_to_dict(obj: Any) -> Any:
    """Recursively convert pydantic models / dataclasses to JSON-safe dicts."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, (list, tuple)):
        return [_model_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _model_to_dict(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_all_resources(server: Server, bot: BotRuntime) -> None:
    resource_defs: list[Resource] = [
        *guild_resources(),
        *channel_resources(),
        *message_resources(),
        *automation_resources(),
    ]

    @server.list_resources()
    async def _list_resources():
        return resource_defs

    @server.read_resource()
    async def _read_resource(uri: Any) -> str:
        uri_str = str(uri)
        log.debug("read_resource uri=%s", uri_str)

        # discord://guilds
        if _GUILDS_RE.match(uri_str):
            guilds = await bot.list_guilds()
            return json.dumps(_model_to_dict(guilds), indent=2)

        # discord://channels/{guild_id}
        m = _CHANNELS_RE.match(uri_str)
        if m:
            guild_id = m.group("guild_id")
            channels = await bot.list_channels(guild_id)
            return json.dumps(_model_to_dict(channels), indent=2)

        # discord://messages/{channel_id}
        m = _MESSAGES_RE.match(uri_str)
        if m:
            channel_id = m.group("channel_id")
            messages = await bot.list_recent_messages(channel_id)
            return json.dumps(_model_to_dict(messages), indent=2)

        # discord://automations/{guild_id}
        m = _AUTOMATIONS_RE.match(uri_str)
        if m:
            guild_id = m.group("guild_id")
            # Automations are currently draft-only; return a placeholder.
            return json.dumps(
                {
                    "guild_id": guild_id,
                    "automations": [],
                    "note": "Automations are draft-only in the current MVP.",
                },
                indent=2,
            )

        raise ValueError(f"unknown resource URI: {uri_str}")
