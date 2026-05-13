# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from discord_mcp_platform.app.logging import setup_logging, get_logger
from discord_mcp_platform.app.settings import settings
from discord_mcp_platform.app.bot_state import get_bot, set_bot
from discord_mcp_platform.api.routes.health import router as health_router
from discord_mcp_platform.api.routes.auth_discord import router as auth_router
from discord_mcp_platform.api.routes.workspaces import router as workspaces_router
from discord_mcp_platform.api.routes.guilds import router as guilds_router
from discord_mcp_platform.api.routes.bots import router as bots_router
from discord_mcp_platform.api.routes.automations import router as automations_router
from discord_mcp_platform.api.routes.audit import router as audit_router
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.errors import (
    AppError,
    AuthenticationError,
    AuthorizationError,
    PolicyDeniedError,
    DiscordPermissionError,
    DiscordNotFoundError,
    RateLimitError,
    ExternalServiceError,
    ValidationError,
)

log = get_logger("app")

_mcp_session_manager = None
_gateway = None
_engine = None
_scheduler = None
_agent_service = None
_slash_handler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mcp_session_manager, _gateway, _engine, _scheduler, _agent_service, _slash_handler
    setup_logging(settings.log_level)
    log.info("starting", app=settings.app_name, transport=settings.mcp_transport)

    if settings.database_url:
        from discord_mcp_platform.db.base import Base
        from discord_mcp_platform.db.models import User, Workspace
        from discord_mcp_platform.app.lifecycle import engine, async_session_factory

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("database_tables_created")

        # Seed system user and workspace for audit logging
        async with async_session_factory() as session:
            from sqlalchemy import select

            exists = (
                await session.execute(select(Workspace).where(Workspace.id == "system"))
            ).scalar_one_or_none()
            if not exists:
                sys_user = (
                    await session.execute(select(User).where(User.id == "system"))
                ).scalar_one_or_none()
                if not sys_user:
                    sys_user = User(discord_user_id="0", username="system")
                    sys_user.id = "system"
                    session.add(sys_user)
                    await session.flush()
                ws = Workspace(name="System", slug="system", owner_user_id="system")
                ws.id = "system"
                session.add(ws)
                await session.commit()
                log.info("system_workspace_seeded")

    if settings.discord_bot_token:
        bot = BotRuntime(settings.discord_bot_token)
        bot._allowed_guilds = settings.allowed_guild_ids
        bot._allowed_channels = settings.allowed_channel_ids
        try:
            await bot.start()
            set_bot(bot)
            log.info("bot_started", bot_id=bot.bot_id)
        except Exception as e:
            log.warning("bot_start_failed", error=str(e))

    # Register slash commands for all guilds
    if settings.database_url and get_bot() is not None:
        from discord_mcp_platform.discord.slash_commands import SlashCommandHandler
        from discord_mcp_platform.app.lifecycle import async_session_factory

        _slash_handler = SlashCommandHandler(get_bot(), async_session_factory)
        try:
            guilds = await get_bot().list_guilds()
            guild_ids = [g.id for g in guilds]
            await _slash_handler.register_commands(guild_ids)
        except Exception as e:
            log.warning("slash_commands_register_failed", error=str(e))

    # Start Discord Gateway for real-time events
    if settings.discord_bot_token and settings.enable_gateway:
        from discord_mcp_platform.discord.gateway import DiscordGateway

        _gateway = DiscordGateway(settings.discord_bot_token)

        if settings.database_url and get_bot() is not None:
            from discord_mcp_platform.automations.engine import AutomationEngine
            import json as _json

            _engine = AutomationEngine(get_bot())

            async def _on_gateway_event(event: dict):
                """Handle Discord Gateway events through the automation engine and agent."""
                event_type = event.get("event_type")

                # Handle slash command interactions
                if event_type == "INTERACTION_CREATE" and _slash_handler is not None:
                    try:
                        handled = await _slash_handler.handle_interaction(event)
                        if handled:
                            return
                    except Exception as e:
                        log.warning("slash_interaction_error", error=str(e))

                if event_type in ("MESSAGE_CREATE", "MESSAGE_UPDATE"):
                    log.info(
                        "gateway_event_received",
                        event_type=event_type,
                        channel_id=event.get("channel_id"),
                        author=event.get("author", {}).get("id"),
                    )

                # Pass event to agent service first (independent of automations)
                if _agent_service is not None:
                    try:
                        await _agent_service.handle_message(event)
                    except Exception as e:
                        log.warning("agent_handler_error", error=str(e))

                try:
                    from discord_mcp_platform.app.lifecycle import async_session_factory
                    from discord_mcp_platform.db.models import Automation
                    from sqlalchemy import select

                    async with async_session_factory() as session:
                        guild_id = event.get("guild_id")
                        if not guild_id:
                            return
                        stmt = select(Automation).where(Automation.guild_id == str(guild_id))
                        result = await session.execute(stmt)
                        automations = result.scalars().all()
                        if not automations:
                            return
                        automation_dicts = [
                            {
                                "id": a.id,
                                "trigger_type": a.trigger_type,
                                "trigger_config": (
                                    _json.loads(a.trigger_config)
                                    if isinstance(a.trigger_config, str)
                                    else (a.trigger_config or {})
                                ),
                                "action_type": a.action_type,
                                "action_config": (
                                    _json.loads(a.action_config)
                                    if isinstance(a.action_config, str)
                                    else (a.action_config or {})
                                ),
                            }
                            for a in automations
                        ]
                        await _engine.evaluate(automation_dicts, event)
                except Exception as e:
                    log.warning("gateway_event_handler_error", error=str(e))

            _gateway.set_event_callback(_on_gateway_event)

        _gateway_task = asyncio.create_task(_gateway.connect())
        log.info("gateway_started")

    # Initialize agent service
    if settings.agent_enabled and settings.agent_api_key and get_bot() is not None:
        from discord_mcp_platform.services.agent_service import AgentService
        from discord_mcp_platform.security.allowlist import Allowlist

        allowlist = Allowlist(
            guild_ids=settings.allowed_guild_ids,
            channel_ids=settings.allowed_channel_ids,
        )

        agent_session_factory = None
        if settings.database_url:
            from discord_mcp_platform.app.lifecycle import async_session_factory

            agent_session_factory = async_session_factory

        _agent_service = AgentService(
            bot=get_bot(),
            allowlist=allowlist,
            api_base_url=settings.agent_api_base_url,
            api_key=settings.agent_api_key,
            model=settings.agent_model,
            system_prompt=settings.agent_system_prompt,
            max_history=settings.agent_max_history,
            cooldown_seconds=settings.agent_cooldown_seconds,
            session_factory=agent_session_factory,
        )
        log.info("agent_service_initialized")

    # Start automation scheduler
    if settings.database_url:
        from discord_mcp_platform.automations.scheduler import AutomationScheduler
        import json as _json

        _scheduler = AutomationScheduler()

        async def _scheduler_tick(context: dict):
            """Periodic tick that checks scheduled automations."""
            if not _engine:
                return
            try:
                from discord_mcp_platform.app.lifecycle import async_session_factory
                from discord_mcp_platform.db.models import Automation
                from sqlalchemy import select

                async with async_session_factory() as session:
                    stmt = select(Automation)
                    result = await session.execute(stmt)
                    automations = result.scalars().all()
                    if not automations:
                        return
                    automation_dicts = [
                        {
                            "id": a.id,
                            "trigger_type": a.trigger_type,
                            "trigger_config": (
                                _json.loads(a.trigger_config)
                                if isinstance(a.trigger_config, str)
                                else (a.trigger_config or {})
                            ),
                            "action_type": a.action_type,
                            "action_config": (
                                _json.loads(a.action_config)
                                if isinstance(a.action_config, str)
                                else (a.action_config or {})
                            ),
                        }
                        for a in automations
                    ]
                    await _engine.evaluate(automation_dicts, context)
            except Exception as e:
                log.warning("scheduler_tick_error", error=str(e))

        _scheduler_task = asyncio.create_task(
            _scheduler.start(interval_seconds=60, tick_callback=_scheduler_tick)
        )
        log.info("automation_scheduler_started")

    try:
        if settings.mcp_transport == "http" and get_bot() is not None:
            from discord_mcp_platform.mcp.server import create_session_manager

            _mcp_session_manager = create_session_manager(get_bot())
            async with _mcp_session_manager.run():
                log.info("mcp_http_server_started")
                yield
        else:
            yield
    finally:
        if _agent_service is not None:
            await _agent_service.close()
            log.info("agent_service_stopped")
        if _scheduler is not None:
            _scheduler.stop()
            log.info("automation_scheduler_stopped")
        if _gateway is not None:
            await _gateway.disconnect()
            log.info("gateway_stopped")
        bot = get_bot()
        if bot is not None:
            await bot.close()
            log.info("bot_stopped")
        set_bot(None)

    log.info("stopping", app=settings.app_name)


app = FastAPI(
    title="Discord MCP Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)


@app.exception_handler(AuthenticationError)
async def _auth_error(request: Request, exc: AuthenticationError):
    return JSONResponse(
        status_code=401, content={"error": "authentication_failed", "detail": str(exc)}
    )


@app.exception_handler(AuthorizationError)
async def _authz_error(request: Request, exc: AuthorizationError):
    return JSONResponse(status_code=403, content={"error": "forbidden", "detail": str(exc)})


@app.exception_handler(PolicyDeniedError)
async def _policy_error(request: Request, exc: PolicyDeniedError):
    return JSONResponse(status_code=403, content={"error": "policy_denied", "detail": str(exc)})


@app.exception_handler(DiscordPermissionError)
async def _discord_perm_error(request: Request, exc: DiscordPermissionError):
    return JSONResponse(
        status_code=403, content={"error": "discord_permission_denied", "detail": str(exc)}
    )


@app.exception_handler(DiscordNotFoundError)
async def _not_found_error(request: Request, exc: DiscordNotFoundError):
    return JSONResponse(status_code=404, content={"error": "not_found", "detail": str(exc)})


@app.exception_handler(RateLimitError)
async def _rate_limit_error(request: Request, exc: RateLimitError):
    headers = {}
    if exc.retry_after is not None:
        headers["Retry-After"] = str(exc.retry_after)
    return JSONResponse(
        status_code=429,
        content={"error": "rate_limited", "detail": str(exc)},
        headers=headers,
    )


@app.exception_handler(ValidationError)
async def _validation_error(request: Request, exc: ValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_failed", "detail": str(exc)})


@app.exception_handler(ExternalServiceError)
async def _external_error(request: Request, exc: ExternalServiceError):
    log.error("external_service_error", detail=str(exc))
    return JSONResponse(status_code=502, content={"error": "external_service_error"})


@app.exception_handler(AppError)
async def _generic_app_error(request: Request, exc: AppError):
    log.error("unhandled_app_error", error=type(exc).__name__, detail=str(exc))
    return JSONResponse(status_code=500, content={"error": "internal_error"})


app.include_router(health_router)
app.include_router(auth_router, prefix="/auth/discord", tags=["auth"])
app.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
app.include_router(guilds_router, prefix="/guilds", tags=["guilds"])
app.include_router(bots_router, prefix="/bots", tags=["bots"])
app.include_router(automations_router, prefix="/automations", tags=["automations"])
app.include_router(audit_router, prefix="/audit", tags=["audit"])


async def _mcp_asgi_app(scope, receive, send):
    if _mcp_session_manager is not None:
        await _mcp_session_manager.handle_request(scope, receive, send)
    else:
        await send(
            {
                "type": "http.response.start",
                "status": 503,
                "headers": [[b"content-type", b"application/json"]],
            }
        )
        await send({"type": "http.response.body", "body": b'{"error":"mcp_server_not_configured"}'})


app.mount("/mcp", app=_mcp_asgi_app)
