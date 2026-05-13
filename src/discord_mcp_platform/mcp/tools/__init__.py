from __future__ import annotations

from collections.abc import Awaitable, Callable

from mcp.server import Server
from mcp.types import TextContent, Tool

from discord_mcp_platform.services.guild_service import GuildService
from discord_mcp_platform.services.channel_service import ChannelService
from discord_mcp_platform.services.message_service import MessageService
from discord_mcp_platform.services.thread_service import ThreadService
from discord_mcp_platform.services.audit_service import AuditService
from discord_mcp_platform.services.automation_service import AutomationService
from discord_mcp_platform.services.role_service import RoleService
from discord_mcp_platform.services.member_service import MemberService
from discord_mcp_platform.services.moderation_service import ModerationService
from discord_mcp_platform.services.webhook_service import WebhookService
from discord_mcp_platform.services.invite_service import InviteService

from discord_mcp_platform.mcp.tools.guilds import (
    get_tools as guild_tools,
    get_handler as guild_handler,
)
from discord_mcp_platform.mcp.tools.channels import (
    get_tools as channel_tools,
    get_handler as channel_handler,
)
from discord_mcp_platform.mcp.tools.messages import (
    get_tools as message_tools,
    get_handler as message_handler,
)
from discord_mcp_platform.mcp.tools.threads import (
    get_tools as thread_tools,
    get_handler as thread_handler,
)
from discord_mcp_platform.mcp.tools.automations import (
    get_tools as automation_tools,
    get_handler as automation_handler,
)
from discord_mcp_platform.mcp.tools.roles import (
    get_tools as role_tools,
    get_handler as role_handler,
)
from discord_mcp_platform.mcp.tools.members import (
    get_tools as member_tools,
    get_handler as member_handler,
)
from discord_mcp_platform.mcp.tools.moderation import (
    get_tools as moderation_tools,
    get_handler as moderation_handler,
)
from discord_mcp_platform.mcp.tools.webhooks import (
    get_tools as webhook_tools,
    get_handler as webhook_handler,
)
from discord_mcp_platform.mcp.tools.invites import (
    get_tools as invite_tools,
    get_handler as invite_handler,
)
from discord_mcp_platform.mcp.tools.audit import (
    get_tools as audit_tools,
    get_handler as audit_handler,
)


def register_all_tools(
    server: Server,
    *,
    guild_service: GuildService,
    channel_service: ChannelService,
    message_service: MessageService,
    thread_service: ThreadService,
    audit_service: AuditService,
    automation_service: AutomationService,
    role_service: RoleService,
    member_service: MemberService,
    moderation_service: ModerationService,
    webhook_service: WebhookService,
    invite_service: InviteService,
) -> None:
    tool_defs: list[Tool] = [
        *guild_tools(),
        *channel_tools(),
        *message_tools(),
        *thread_tools(),
        *automation_tools(),
        *role_tools(),
        *member_tools(),
        *moderation_tools(),
        *webhook_tools(),
        *invite_tools(),
        *audit_tools(),
    ]

    handlers: list[Callable[[str, dict], Awaitable[list[TextContent] | None]]] = [
        guild_handler(guild_service, audit_service),
        channel_handler(channel_service, audit_service),
        message_handler(message_service, audit_service),
        thread_handler(thread_service, audit_service),
        automation_handler(automation_service, audit_service),
        role_handler(role_service, audit_service),
        member_handler(member_service, audit_service),
        moderation_handler(moderation_service, audit_service),
        webhook_handler(webhook_service, audit_service),
        invite_handler(invite_service, audit_service),
        audit_handler(audit_service),
    ]

    @server.list_tools()
    async def _list_tools():
        return tool_defs

    @server.call_tool()
    async def _call_tool(name: str, arguments: dict):
        for handler in handlers:
            result = await handler(name, arguments)
            if result is not None:
                return result
        raise ValueError(f"unknown tool: {name}")
