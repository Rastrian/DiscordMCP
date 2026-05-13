# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from contextvars import ContextVar

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.mcp.context import MCPContext
from discord_mcp_platform.security.policy import PermissionService
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
from discord_mcp_platform.mcp.tools import register_all_tools
from discord_mcp_platform.mcp.resources import register_all_resources
from discord_mcp_platform.mcp.prompts import register_all_prompts

log = get_logger("mcp_server")

# Context variable holding the authenticated MCP principal for the
# current request.  Tools and resource handlers can read this to find
# out who is calling.
mcp_request_context: ContextVar[MCPContext | None] = ContextVar(
    "mcp_request_context",
    default=None,
)


def _extract_token(params: object) -> str | None:
    """Extract an MCP client token from request params ``_meta``.

    The MCP SDK allows arbitrary extra fields on the ``_meta`` dict
    (``RequestParams.Meta`` uses ``extra="allow"``).  We look for an
    ``x-mcp-token`` key there.
    """
    meta = getattr(params, "meta", None)
    if meta is None:
        return None
    # meta may be a RequestParams.Meta instance or a plain dict.
    if isinstance(meta, dict):
        return meta.get("x-mcp-token")
    return getattr(meta, "x-mcp-token", None)


async def _resolve_mcp_context(token: str | None) -> MCPContext | None:
    """Validate *token* against the MCP client store and return a context.

    If *token* is ``None`` or empty the call is allowed through
    (development / unauthenticated mode) and ``None`` is returned so
    that callers can distinguish "no auth" from "authenticated".
    """
    if not token:
        return None

    # Import here to avoid a hard dependency on the DB layer at module
    # load time -- tests and stdio mode may not have a session factory.
    from discord_mcp_platform.app.lifecycle import async_session_factory
    from discord_mcp_platform.control_plane.mcp_clients import MCPClientService
    from discord_mcp_platform.mcp.auth import MCPAuth

    async with async_session_factory() as session:
        svc = MCPClientService(session)
        auth = MCPAuth(svc)
        client = await auth.authenticate(token)

    return MCPContext(
        workspace_id=client["id"],
        mcp_client_id=client["id"],
        scopes=client.get("scopes", ""),
    )


def create_mcp_server(bot: BotRuntime) -> Server:
    server = Server("discord-mcp-platform")

    # --- Auth middleware ---------------------------------------------------
    # Wrap the call_tool / read_resource handlers so every request first
    # resolves the MCP context from a token carried in request _meta.

    def _install_auth_middleware() -> None:
        # Grab the handler registered by register_all_tools below.
        # The MCP SDK stores handlers in server.request_handlers keyed
        # by the request type.
        from mcp.types import CallToolRequest, ReadResourceRequest

        original_tool_handler = server.request_handlers.get(CallToolRequest)
        original_resource_handler = server.request_handlers.get(ReadResourceRequest)

        async def _authenticated_tool_handler(req: CallToolRequest):  # type: ignore[valid-type]
            token = _extract_token(req.params)
            ctx = await _resolve_mcp_context(token)
            mcp_request_context.set(ctx)
            if original_tool_handler is not None:
                return await original_tool_handler(req)

        async def _authenticated_resource_handler(req: ReadResourceRequest):  # type: ignore[valid-type]
            token = _extract_token(req.params)
            ctx = await _resolve_mcp_context(token)
            mcp_request_context.set(ctx)
            if original_resource_handler is not None:
                return await original_resource_handler(req)

        server.request_handlers[CallToolRequest] = _authenticated_tool_handler
        server.request_handlers[ReadResourceRequest] = _authenticated_resource_handler

    # --- Services ----------------------------------------------------------

    permissions = PermissionService(bot._allowed_guilds, bot._allowed_channels)

    from discord_mcp_platform.app.lifecycle import async_session_factory

    guild_svc = GuildService(bot, permissions)
    channel_svc = ChannelService(bot, permissions)
    message_svc = MessageService(bot, permissions)
    thread_svc = ThreadService(bot, permissions)
    audit_svc = AuditService(session_factory=async_session_factory)
    automation_svc = AutomationService(session_factory=async_session_factory)
    role_svc = RoleService(bot, permissions)
    member_svc = MemberService(bot, permissions)
    moderation_svc = ModerationService(bot, permissions)
    webhook_svc = WebhookService(bot, permissions)
    invite_svc = InviteService(bot, permissions)

    register_all_tools(
        server,
        guild_service=guild_svc,
        channel_service=channel_svc,
        message_service=message_svc,
        thread_service=thread_svc,
        audit_service=audit_svc,
        automation_service=automation_svc,
        role_service=role_svc,
        member_service=member_svc,
        moderation_service=moderation_svc,
        webhook_service=webhook_svc,
        invite_service=invite_svc,
    )
    register_all_resources(server, bot)
    register_all_prompts(server)

    # Install auth middleware *after* all handlers are registered so
    # we can wrap the final versions.
    _install_auth_middleware()

    return server


def create_session_manager(bot: BotRuntime) -> StreamableHTTPSessionManager:
    server = create_mcp_server(bot)
    return StreamableHTTPSessionManager(app=server, stateless=True)


async def run_stdio(bot: BotRuntime) -> None:
    server = create_mcp_server(bot)
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())
