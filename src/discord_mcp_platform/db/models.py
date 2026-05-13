# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from discord_mcp_platform.db.base import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid4_str() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    discord_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    username: Mapped[str] = mapped_column(String)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    access_token: Mapped[str] = mapped_column(String)
    provider: Mapped[str] = mapped_column(String, default="discord")
    refresh_token: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    token_expires_at: Mapped[datetime | None] = mapped_column(nullable=True, default=None)
    scopes: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    name: Mapped[str] = mapped_column(String)
    slug: Mapped[str] = mapped_column(String, unique=True, index=True)
    owner_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class WorkspaceMembership(Base):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_user"),)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    role: Mapped[str] = mapped_column(String, default="viewer")
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)


class GuildInstallation(Base):
    __tablename__ = "guild_installations"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    guild_id: Mapped[str] = mapped_column(String, index=True)
    bot_installed: Mapped[bool] = mapped_column(default=False)
    installed_by_user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, default=None
    )
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class MCPClient(Base):
    __tablename__ = "mcp_clients"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    name: Mapped[str] = mapped_column(String)
    token_hash: Mapped[str] = mapped_column(String)
    scopes: Mapped[str] = mapped_column(String, default="")
    active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    guild_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    channel_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    permission_flags: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="viewer")
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class GuildPolicy(Base):
    __tablename__ = "guild_policies"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    guild_id: Mapped[str] = mapped_column(String, index=True)
    permission_flags: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="viewer")
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class ChannelPolicy(Base):
    __tablename__ = "channel_policies"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    guild_id: Mapped[str] = mapped_column(String)
    channel_id: Mapped[str] = mapped_column(String, index=True)
    permission_flags: Mapped[str] = mapped_column(String, default="")
    role: Mapped[str] = mapped_column(String, default="viewer")
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    action: Mapped[str] = mapped_column(String)
    user_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    mcp_client_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    guild_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    channel_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    target_id: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    details: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)


class Automation(Base):
    __tablename__ = "automations"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"))
    guild_id: Mapped[str] = mapped_column(String)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    trigger_type: Mapped[str] = mapped_column(String)
    action_type: Mapped[str] = mapped_column(String)
    trigger_config: Mapped[str] = mapped_column(String, default="{}")
    action_config: Mapped[str] = mapped_column(String, default="{}")
    target_channel_ids: Mapped[str] = mapped_column(String, default="[]")
    status: Mapped[str] = mapped_column(String, default="draft")
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class BotConfig(Base):
    __tablename__ = "bot_configs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default_factory=_uuid4_str, init=False
    )
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    bot_token_hash: Mapped[str | None] = mapped_column(String(128), nullable=True, default=None)
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(default_factory=_utcnow, onupdate=_utcnow)


class AllowedChatChannel(Base):
    __tablename__ = "allowed_chat_channels"
    __table_args__ = (UniqueConstraint("guild_id", "channel_id", name="uq_guild_channel"),)

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default_factory=_uuid4_str, init=False
    )
    guild_id: Mapped[str] = mapped_column(String, index=True)
    channel_id: Mapped[str] = mapped_column(String, index=True)
    allowed_by_user_id: Mapped[str] = mapped_column(String)
    channel_name: Mapped[str | None] = mapped_column(String, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(default_factory=_utcnow)
