# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from discord_mcp_platform.app.lifecycle import get_db_session
from discord_mcp_platform.app.settings import settings
from discord_mcp_platform.discord.oauth import DiscordOAuth
from discord_mcp_platform.db.models import User, OAuthAccount, Workspace

router = APIRouter()

_oauth = DiscordOAuth(
    client_id=settings.discord_client_id,
    client_secret=settings.discord_client_secret,
    redirect_uri=settings.discord_redirect_uri,
)


@router.get("/login")
async def discord_login(request: Request):
    state = _oauth.generate_state()
    request.session["oauth_state"] = state
    url = _oauth.get_authorize_url(state)
    return RedirectResponse(url=url)


@router.get("/callback")
async def discord_callback(request: Request, session: AsyncSession = Depends(get_db_session)):
    code = request.query_params.get("code")
    state = request.query_params.get("state")
    expected_state = request.session.get("oauth_state")

    if not code or not state or not expected_state:
        return {"error": "missing_code_or_state"}

    if not _oauth.validate_state(state, expected_state):
        return {"error": "invalid_state"}

    try:
        token_data = await _oauth.exchange_code(code)
        profile = await _oauth.fetch_user_profile(token_data["access_token"])
    except Exception:
        return {"error": "oauth_exchange_failed"}

    discord_id = profile.get("id", "")
    username = profile.get("username", "")
    display_name = profile.get("global_name")
    avatar = profile.get("avatar")
    avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png" if avatar else None

    now = datetime.now(timezone.utc)

    # Upsert user
    stmt = select(User).where(User.discord_user_id == discord_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            discord_user_id=discord_id,
            username=username,
            display_name=display_name,
            avatar_url=avatar_url,
        )
        session.add(user)
        await session.flush()

        # Create personal workspace
        workspace = Workspace(
            name=f"{username}'s workspace",
            slug=f"{username}-{discord_id[:8]}",
            owner_user_id=user.id,
        )
        session.add(workspace)
    else:
        user.username = username
        user.display_name = display_name
        user.avatar_url = avatar_url
        user.updated_at = now

    # Upsert OAuth account
    stmt = select(OAuthAccount).where(
        OAuthAccount.user_id == user.id,
        OAuthAccount.provider == "discord",
    )
    result = await session.execute(stmt)
    oauth_account = result.scalar_one_or_none()

    if oauth_account is None:
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider="discord",
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expires_at=datetime.fromtimestamp(
                token_data.get("expires_at", 0), tz=timezone.utc
            )
            if token_data.get("expires_at")
            else None,
            scopes=token_data.get("scope"),
        )
        session.add(oauth_account)
    else:
        oauth_account.access_token = token_data["access_token"]
        oauth_account.refresh_token = token_data.get("refresh_token")
        oauth_account.token_expires_at = (
            datetime.fromtimestamp(token_data.get("expires_at", 0), tz=timezone.utc)
            if token_data.get("expires_at")
            else None
        )
        oauth_account.scopes = token_data.get("scope")
        oauth_account.updated_at = now

    await session.flush()

    request.session["user_id"] = user.id
    request.session["discord_user_id"] = discord_id
    request.session["username"] = username

    return {
        "status": "ok",
        "user": {"id": user.id, "discord_id": discord_id, "username": username},
    }
