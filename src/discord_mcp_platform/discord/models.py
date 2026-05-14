# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from pydantic import BaseModel, Field


class DiscordGuild(BaseModel):
    id: str
    name: str
    icon: str | None = None
    owner: bool = False


class DiscordPermissionOverwrite(BaseModel):
    id: str
    type: int
    allow: str = "0"
    deny: str = "0"


class DiscordChannel(BaseModel):
    id: str
    guild_id: str
    name: str
    type: int = 0
    topic: str | None = None
    permission_overwrites: list[DiscordPermissionOverwrite] = Field(default_factory=list)
    parent_id: str | None = None
    position: int = 0
    nsfw: bool = False
    rate_limit_per_user: int = 0
    bitrate: int | None = None
    user_limit: int | None = None


class DiscordMessage(BaseModel):
    id: str
    channel_id: str
    author_id: str
    author_name: str
    content: str
    timestamp: str


class DiscordThread(BaseModel):
    id: str
    channel_id: str
    guild_id: str
    name: str
    private: bool = False


class DiscordRole(BaseModel):
    id: str
    guild_id: str
    name: str
    color: int = 0
    hoist: bool = False
    position: int = 0
    permissions: str = "0"
    mentionable: bool = False


class DiscordWebhook(BaseModel):
    id: str
    channel_id: str
    guild_id: str = ""
    name: str
    avatar: str | None = None
    token: str | None = None


class DiscordInvite(BaseModel):
    code: str
    guild_id: str = ""
    channel_id: str = ""
    inviter_id: str = ""
    uses: int = 0
    max_uses: int = 0
    temporary: bool = False
    expires_at: str | None = None


class GuildListInput(BaseModel):
    pass


class GuildListOutput(BaseModel):
    guilds: list[DiscordGuild]


class GuildGetInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")


class GuildModifyInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str | None = None
    dry_run: bool = True
    confirmation: str | None = None


class ChannelListInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")


class ChannelListOutput(BaseModel):
    guild_id: str
    channels: list[DiscordChannel]


class ChannelGetInput(BaseModel):
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")


class ChannelGetOutput(BaseModel):
    channel: DiscordChannel


class ChannelCreateInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str = Field(min_length=1, max_length=100)
    channel_type: int = 0
    topic: str | None = None
    parent_id: str | None = Field(default=None, pattern=r"^[0-9]{15,25}$")
    nsfw: bool = False
    rate_limit_per_user: int = Field(default=0, ge=0, le=21600)
    bitrate: int | None = None
    user_limit: int | None = None
    permission_overwrites: list[DiscordPermissionOverwrite] = Field(default_factory=list)
    dry_run: bool = True
    confirmation: str | None = None


class ChannelCreateOutput(BaseModel):
    status: str
    dry_run: bool
    channel_id: str | None = None


class ChannelEditInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str | None = Field(default=None, min_length=1, max_length=100)
    topic: str | None = None
    parent_id: str | None = Field(default=None, pattern=r"^[0-9]{15,25}$")
    nsfw: bool | None = None
    rate_limit_per_user: int | None = Field(default=None, ge=0, le=21600)
    bitrate: int | None = None
    user_limit: int | None = None
    dry_run: bool = True
    confirmation: str | None = None


class ChannelEditOutput(BaseModel):
    status: str
    dry_run: bool
    channel_id: str | None = None


class ChannelDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class ChannelPermissionsEditInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    overwrite_id: str = Field(pattern=r"^[0-9]{15,25}$")
    overwrite_type: int = Field(ge=0, le=1)
    allow: str = "0"
    deny: str = "0"
    dry_run: bool = True
    confirmation: str | None = None


class ChannelPermissionsDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    overwrite_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class RoleListInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")


class RoleListOutput(BaseModel):
    guild_id: str
    roles: list[DiscordRole]


class RoleCreateInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str = Field(min_length=1, max_length=100)
    color: int = 0
    hoist: bool = False
    permissions: str = "0"
    mentionable: bool = False
    dry_run: bool = True
    confirmation: str | None = None


class RoleModifyInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    role_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str | None = None
    color: int | None = None
    hoist: bool | None = None
    permissions: str | None = None
    mentionable: bool | None = None
    dry_run: bool = True
    confirmation: str | None = None


class RoleDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    role_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class RoleAssignInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")
    role_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class RoleRemoveInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")
    role_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class MemberGetInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")


class MemberListInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    limit: int = Field(default=100, ge=1, le=1000)


class MemberTimeoutInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")
    duration_seconds: int = Field(ge=1, le=2419200)
    dry_run: bool = True
    confirmation: str | None = None


class MemberUnbanInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class MemberKickInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class MemberBanInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    user_id: str = Field(pattern=r"^[0-9]{15,25}$")
    delete_message_days: int = Field(default=0, ge=0, le=7)
    dry_run: bool = True
    confirmation: str | None = None


class MessageListRecentInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    limit: int = Field(default=50, ge=1, le=100)


class MessageListRecentOutput(BaseModel):
    channel_id: str
    messages: list[DiscordMessage]


class MessageGetInput(BaseModel):
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    message_id: str = Field(pattern=r"^[0-9]{15,25}$")


class MessageSendInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    content: str = Field(min_length=1, max_length=2000)
    dry_run: bool = True
    confirmation: str | None = None


class MessageSendOutput(BaseModel):
    status: str
    dry_run: bool
    message_id: str | None = None


class MessageEditInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    message_id: str = Field(pattern=r"^[0-9]{15,25}$")
    content: str = Field(min_length=1, max_length=2000)
    dry_run: bool = True
    confirmation: str | None = None


class MessageDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    message_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class MessageBulkDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    message_ids: list[str] = Field(min_length=2, max_length=100)
    dry_run: bool = True
    confirmation: str | None = None


class MessageSendEmbedInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    content: str | None = None
    embeds: list[dict] = Field(min_length=1, max_length=10)
    dry_run: bool = True
    confirmation: str | None = None


class MessageSendEmbedOutput(BaseModel):
    status: str
    dry_run: bool
    message_id: str | None = None


class ReactionAddInput(BaseModel):
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    message_id: str = Field(pattern=r"^[0-9]{15,25}$")
    emoji: str = Field(min_length=1, max_length=100)


class ReactionRemoveInput(BaseModel):
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    message_id: str = Field(pattern=r"^[0-9]{15,25}$")
    emoji: str = Field(min_length=1, max_length=100)


class ThreadCreateInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str = Field(min_length=1, max_length=100)
    message_id: str | None = Field(default=None, pattern=r"^[0-9]{15,25}$")
    private: bool = False
    dry_run: bool = True
    confirmation: str | None = None


class ThreadCreateOutput(BaseModel):
    status: str
    dry_run: bool
    thread_id: str | None = None


class WebhookCreateInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str = Field(min_length=1, max_length=80)
    dry_run: bool = True
    confirmation: str | None = None


class WebhookListInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")


class WebhookModifyInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    webhook_id: str = Field(pattern=r"^[0-9]{15,25}$")
    name: str | None = None
    channel_id: str | None = Field(default=None, pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class WebhookDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    webhook_id: str = Field(pattern=r"^[0-9]{15,25}$")
    dry_run: bool = True
    confirmation: str | None = None


class WebhookExecuteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    webhook_id: str = Field(pattern=r"^[0-9]{15,25}$")
    webhook_token: str = Field(min_length=1)
    content: str = Field(min_length=1, max_length=2000)
    username: str | None = None
    dry_run: bool = True
    confirmation: str | None = None


class InviteCreateInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    channel_id: str = Field(pattern=r"^[0-9]{15,25}$")
    max_age: int = Field(default=86400, ge=0, le=604800)
    max_uses: int = Field(default=0, ge=0, le=100)
    temporary: bool = False
    dry_run: bool = True
    confirmation: str | None = None


class InviteListInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")


class InviteGetInput(BaseModel):
    code: str = Field(min_length=1, max_length=16)


class InviteDeleteInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    code: str = Field(min_length=1, max_length=16)
    dry_run: bool = True
    confirmation: str | None = None


class AutomationDraftInput(BaseModel):
    guild_id: str = Field(pattern=r"^[0-9]{15,25}$")
    description: str = Field(min_length=1, max_length=2000)
    target_channel_ids: list[str] = Field(default_factory=list)
    workspace_id: str = "default"


class AutomationDraftOutput(BaseModel):
    status: str
    draft_id: str | None = None
    summary: str
