# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.models import (
    DiscordChannel,
    DiscordGuild,
    DiscordInvite,
    DiscordMessage,
    DiscordPermissionOverwrite,
    DiscordRole,
    DiscordThread,
    DiscordWebhook,
)
from discord_mcp_platform.discord.rest_client import DiscordRestClient
from discord_mcp_platform.app.settings import settings


class BotRuntime:
    def __init__(self, bot_token: str) -> None:
        self._rest_client = DiscordRestClient(bot_token)
        self._bot_token = bot_token

    @property
    def rest(self) -> DiscordRestClient:
        return self._rest_client

    @property
    def bot_id(self) -> str | None:
        return self._bot_id

    def get_invite_url(self, permissions: int = 0, guild_id: str | None = None) -> str:
        scopes = "bot identify guilds"
        client_id = settings.discord_client_id
        url = f"https://discord.com/oauth2/authorize?client_id={client_id}&scope={scopes}"
        if permissions:
            url += f"&permissions={permissions}"
        if guild_id:
            url += f"&guild_id={guild_id}&disable_guild_select=true"
        return url

    def _parse_channel(self, data: dict, guild_id: str = "") -> DiscordChannel:
        return DiscordChannel(
            id=data["id"],
            guild_id=data.get("guild_id", guild_id),
            name=data.get("name", ""),
            type=data.get("type", 0),
            topic=data.get("topic"),
            permission_overwrites=[
                DiscordPermissionOverwrite(
                    id=o["id"],
                    type=o.get("type", 0),
                    allow=str(o.get("allow", "0")),
                    deny=str(o.get("deny", "0")),
                )
                for o in data.get("permission_overwrites", [])
            ],
            parent_id=data.get("parent_id"),
            position=data.get("position", 0),
            nsfw=data.get("nsfw", False),
            rate_limit_per_user=data.get("rate_limit_per_user", 0),
            bitrate=data.get("bitrate"),
            user_limit=data.get("user_limit"),
        )

    # --- Guilds ---

    async def list_guilds(self) -> list[DiscordGuild]:
        data = await self._rest_client.get_guilds()
        return [
            DiscordGuild(
                id=g["id"], name=g["name"], icon=g.get("icon"), owner=g.get("owner", False)
            )
            for g in data
        ]

    async def get_guild(self, guild_id: str) -> DiscordGuild:
        data = await self._rest_client.get_guild(guild_id)
        return DiscordGuild(id=data["id"], name=data["name"], icon=data.get("icon"), owner=False)

    # --- Channels ---

    async def list_channels(self, guild_id: str) -> list[DiscordChannel]:
        data = await self._rest_client.get_channels(guild_id)
        return [self._parse_channel(c, guild_id) for c in data]

    async def get_channel(self, channel_id: str) -> DiscordChannel:
        data = await self._rest_client.get_channel(channel_id)
        return self._parse_channel(data)

    async def create_channel(
        self, guild_id: str, name: str, channel_type: int = 0, **kwargs
    ) -> DiscordChannel:
        data = await self._rest_client.create_channel(guild_id, name, channel_type, **kwargs)
        return self._parse_channel(data, guild_id)

    async def delete_channel(self, channel_id: str) -> None:
        await self._rest_client.delete_channel(channel_id)

    async def modify_channel(self, channel_id: str, **kwargs) -> DiscordChannel:
        data = await self._rest_client.modify_channel(channel_id, **kwargs)
        return self._parse_channel(data)

    async def edit_channel_permissions(
        self, channel_id: str, overwrite_id: str, allow: str, deny: str, overwrite_type: int
    ) -> None:
        await self._rest_client.edit_channel_permissions(
            channel_id, overwrite_id, allow, deny, overwrite_type
        )

    async def delete_channel_permissions(self, channel_id: str, overwrite_id: str) -> None:
        await self._rest_client.delete_channel_permissions(channel_id, overwrite_id)

    # --- Messages ---

    async def list_recent_messages(self, channel_id: str, limit: int = 50) -> list[DiscordMessage]:
        data = await self._rest_client.get_messages(channel_id, limit=limit)
        return [
            DiscordMessage(
                id=m["id"],
                channel_id=channel_id,
                author_id=m["author"]["id"],
                author_name=m["author"].get("global_name") or m["author"].get("username", ""),
                content=m.get("content", ""),
                timestamp=m.get("timestamp", ""),
            )
            for m in data
        ]

    async def send_message(self, channel_id: str, content: str) -> DiscordMessage:
        data = await self._rest_client.send_message(channel_id, content)
        return DiscordMessage(
            id=data["id"],
            channel_id=channel_id,
            author_id=data["author"]["id"],
            author_name=data["author"].get("global_name") or data["author"].get("username", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
        )

    async def send_rich_message(
        self, channel_id: str, content: str | None = None, embeds: list[dict] | None = None
    ) -> DiscordMessage:
        data = await self._rest_client.send_rich_message(channel_id, content, embeds)
        return DiscordMessage(
            id=data["id"],
            channel_id=channel_id,
            author_id=data["author"]["id"],
            author_name=data["author"].get("global_name") or data["author"].get("username", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
        )

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str | None = None,
        embeds: list[dict] | None = None,
    ) -> DiscordMessage:
        data = await self._rest_client.edit_message(channel_id, message_id, content, embeds)
        return DiscordMessage(
            id=data["id"],
            channel_id=channel_id,
            author_id=data["author"]["id"],
            author_name=data["author"].get("global_name") or data["author"].get("username", ""),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", ""),
        )

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        await self._rest_client.delete_message(channel_id, message_id)

    async def bulk_delete_messages(self, channel_id: str, message_ids: list[str]) -> None:
        await self._rest_client.bulk_delete_messages(channel_id, message_ids)

    # --- Threads ---

    async def create_thread(
        self, channel_id: str, name: str, message_id: str | None = None, private: bool = False
    ) -> DiscordThread:
        data = await self._rest_client.create_thread(
            channel_id, name, message_id=message_id, private=private
        )
        return DiscordThread(
            id=data["id"],
            channel_id=channel_id,
            guild_id=data.get("guild_id", ""),
            name=data.get("name", name),
            private=private,
        )

    # --- Members ---

    async def get_member(self, guild_id: str, user_id: str) -> dict:
        return await self._rest_client.get_guild_member(guild_id, user_id)

    async def list_members(self, guild_id: str, limit: int = 100) -> list[dict]:
        return await self._rest_client.list_guild_members(guild_id, limit=limit)

    async def timeout_member(
        self, guild_id: str, user_id: str, communication_disabled_until: str
    ) -> None:
        await self._rest_client.modify_guild_member(
            guild_id, user_id, communication_disabled_until=communication_disabled_until
        )

    async def kick_member(self, guild_id: str, user_id: str) -> None:
        await self._rest_client.kick_member(guild_id, user_id)

    async def ban_member(self, guild_id: str, user_id: str, delete_message_days: int = 0) -> None:
        await self._rest_client.ban_member(
            guild_id, user_id, delete_message_days=delete_message_days
        )

    async def unban_member(self, guild_id: str, user_id: str) -> None:
        await self._rest_client.unban_member(guild_id, user_id)

    # --- Roles ---

    async def list_roles(self, guild_id: str) -> list[dict]:
        return await self._rest_client.list_guild_roles(guild_id)

    async def add_role(self, guild_id: str, user_id: str, role_id: str) -> None:
        await self._rest_client.add_guild_member_role(guild_id, user_id, role_id)

    async def remove_role(self, guild_id: str, user_id: str, role_id: str) -> None:
        await self._rest_client.remove_guild_member_role(guild_id, user_id, role_id)

    async def create_role(self, guild_id: str, **kwargs) -> DiscordRole:
        data = await self._rest_client.create_guild_role(guild_id, **kwargs)
        return DiscordRole(
            id=data["id"],
            guild_id=guild_id,
            name=data["name"],
            color=data.get("color", 0),
            hoist=data.get("hoist", False),
            position=data.get("position", 0),
            permissions=data.get("permissions", "0"),
            mentionable=data.get("mentionable", False),
        )

    async def modify_role(self, guild_id: str, role_id: str, **kwargs) -> DiscordRole:
        data = await self._rest_client.modify_guild_role(guild_id, role_id, **kwargs)
        return DiscordRole(
            id=data["id"],
            guild_id=guild_id,
            name=data["name"],
            color=data.get("color", 0),
            hoist=data.get("hoist", False),
            position=data.get("position", 0),
            permissions=data.get("permissions", "0"),
            mentionable=data.get("mentionable", False),
        )

    async def delete_role(self, guild_id: str, role_id: str) -> None:
        await self._rest_client.delete_guild_role(guild_id, role_id)

    async def reorder_roles(self, guild_id: str, positions: list[dict]) -> list[DiscordRole]:
        data = await self._rest_client.modify_guild_role_positions(guild_id, positions)
        return [
            DiscordRole(
                id=r["id"],
                guild_id=guild_id,
                name=r["name"],
                position=r.get("position", 0),
                permissions=r.get("permissions", "0"),
            )
            for r in data
        ]

    # --- Guild (new) ---

    async def modify_guild(self, guild_id: str, **kwargs) -> DiscordGuild:
        data = await self._rest_client.modify_guild(guild_id, **kwargs)
        return DiscordGuild(id=data["id"], name=data["name"], icon=data.get("icon"), owner=False)

    # --- Webhooks ---

    async def create_webhook(self, channel_id: str, name: str) -> dict:
        return await self._rest_client.create_webhook(channel_id, name)

    async def list_webhooks(self, guild_id: str) -> list[dict]:
        return await self._rest_client.list_guild_webhooks(guild_id)

    async def get_webhook(self, webhook_id: str) -> DiscordWebhook:
        data = await self._rest_client.get_webhook(webhook_id)
        return DiscordWebhook(
            id=data["id"],
            channel_id=data.get("channel_id", ""),
            guild_id=data.get("guild_id", ""),
            name=data.get("name", ""),
            avatar=data.get("avatar"),
        )

    async def modify_webhook(self, webhook_id: str, **kwargs) -> DiscordWebhook:
        data = await self._rest_client.modify_webhook(webhook_id, **kwargs)
        return DiscordWebhook(
            id=data["id"],
            channel_id=data.get("channel_id", ""),
            guild_id=data.get("guild_id", ""),
            name=data.get("name", ""),
            avatar=data.get("avatar"),
        )

    async def delete_webhook(self, webhook_id: str) -> None:
        await self._rest_client.delete_webhook(webhook_id)

    async def execute_webhook(self, webhook_id: str, webhook_token: str, **kwargs) -> dict:
        return await self._rest_client.execute_webhook(webhook_id, webhook_token, **kwargs)

    async def list_channel_webhooks(self, channel_id: str) -> list[DiscordWebhook]:
        data = await self._rest_client.list_channel_webhooks(channel_id)
        return [
            DiscordWebhook(
                id=w["id"],
                channel_id=w.get("channel_id", ""),
                guild_id=w.get("guild_id", ""),
                name=w.get("name", ""),
                avatar=w.get("avatar"),
            )
            for w in data
        ]

    # --- Invites ---

    async def create_invite(self, channel_id: str, **kwargs) -> DiscordInvite:
        data = await self._rest_client.create_channel_invite(channel_id, **kwargs)
        return DiscordInvite(
            code=data["code"],
            channel_id=data.get("channel", {}).get("id", channel_id)
            if isinstance(data.get("channel"), dict)
            else channel_id,
            guild_id=data.get("guild", {}).get("id", "")
            if isinstance(data.get("guild"), dict)
            else "",
            uses=data.get("uses", 0),
            max_uses=data.get("max_uses", 0),
            temporary=data.get("temporary", False),
        )

    async def list_invites(self, guild_id: str) -> list[DiscordInvite]:
        data = await self._rest_client.get_guild_invites(guild_id)
        return [
            DiscordInvite(
                code=i["code"],
                guild_id=guild_id,
                channel_id=i.get("channel", {}).get("id", "")
                if isinstance(i.get("channel"), dict)
                else "",
                uses=i.get("uses", 0),
                max_uses=i.get("max_uses", 0),
                temporary=i.get("temporary", False),
            )
            for i in data
        ]

    async def get_invite(self, code: str) -> DiscordInvite:
        data = await self._rest_client.get_invite(code)
        return DiscordInvite(
            code=data["code"],
            guild_id=data.get("guild", {}).get("id", "")
            if isinstance(data.get("guild"), dict)
            else "",
            channel_id=data.get("channel", {}).get("id", "")
            if isinstance(data.get("channel"), dict)
            else "",
            uses=data.get("uses", 0),
            max_uses=data.get("max_uses", 0),
        )

    async def delete_invite(self, code: str) -> None:
        await self._rest_client.delete_invite(code)

    # --- Pins ---

    async def list_pinned_messages(self, channel_id: str) -> list[dict]:
        return await self._rest_client.get_pinned_messages(channel_id)

    async def pin_message(self, channel_id: str, message_id: str) -> None:
        await self._rest_client.pin_message(channel_id, message_id)

    async def unpin_message(self, channel_id: str, message_id: str) -> None:
        await self._rest_client.unpin_message(channel_id, message_id)

    # --- Reactions ---

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        await self._rest_client.add_reaction(channel_id, message_id, emoji)

    async def remove_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        await self._rest_client.delete_own_reaction(channel_id, message_id, emoji)

    # --- Crosspost ---

    async def crosspost_message(self, channel_id: str, message_id: str) -> dict:
        return await self._rest_client.crosspost_message(channel_id, message_id)

    # --- Active / Archived Threads ---

    async def list_active_threads(self, guild_id: str) -> dict:
        return await self._rest_client.list_active_threads(guild_id)

    async def list_archived_threads(self, channel_id: str, archive_type: str = "public") -> dict:
        if archive_type == "private":
            return await self._rest_client.list_private_archived_threads(channel_id)
        return await self._rest_client.list_public_archived_threads(channel_id)

    # --- Thread Members ---

    async def list_thread_members(self, channel_id: str) -> list[dict]:
        return await self._rest_client.list_thread_members(channel_id)

    # --- Audit Log ---

    async def get_audit_log(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.get_audit_log(guild_id, **kwargs)

    # --- Member Search ---

    async def search_members(self, guild_id: str, query: str, **kwargs) -> list[dict]:
        return await self._rest_client.search_guild_members(guild_id, query, **kwargs)

    # --- Bulk Ban ---

    async def bulk_ban_members(self, guild_id: str, user_ids: list[str], **kwargs) -> dict:
        return await self._rest_client.bulk_ban_members(guild_id, user_ids, **kwargs)

    # --- Prune ---

    async def get_prune_count(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.get_prune_count(guild_id, **kwargs)

    async def begin_prune(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.begin_prune(guild_id, **kwargs)

    # --- Guild Preview ---

    async def get_guild_preview(self, guild_id: str) -> dict:
        return await self._rest_client.get_guild_preview(guild_id)

    # --- Onboarding ---

    async def get_onboarding(self, guild_id: str) -> dict:
        return await self._rest_client.get_guild_onboarding(guild_id)

    async def update_onboarding(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.update_guild_onboarding(guild_id, **kwargs)

    # --- Welcome Screen ---

    async def get_welcome_screen(self, guild_id: str) -> dict:
        return await self._rest_client.get_guild_welcome_screen(guild_id)

    async def update_welcome_screen(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.update_guild_welcome_screen(guild_id, **kwargs)

    # --- Auto-Moderation ---

    async def list_auto_mod_rules(self, guild_id: str) -> list[dict]:
        return await self._rest_client.list_auto_moderation_rules(guild_id)

    async def get_auto_mod_rule(self, guild_id: str, rule_id: str) -> dict:
        return await self._rest_client.get_auto_moderation_rule(guild_id, rule_id)

    async def create_auto_mod_rule(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.create_auto_moderation_rule(guild_id, **kwargs)

    async def update_auto_mod_rule(self, guild_id: str, rule_id: str, **kwargs) -> dict:
        return await self._rest_client.update_auto_moderation_rule(guild_id, rule_id, **kwargs)

    async def delete_auto_mod_rule(self, guild_id: str, rule_id: str) -> None:
        await self._rest_client.delete_auto_moderation_rule(guild_id, rule_id)

    # --- Scheduled Events ---

    async def list_scheduled_events(self, guild_id: str, **kwargs) -> list[dict]:
        return await self._rest_client.list_scheduled_events(guild_id, **kwargs)

    async def get_scheduled_event(self, guild_id: str, event_id: str) -> dict:
        return await self._rest_client.get_scheduled_event(guild_id, event_id)

    async def create_scheduled_event(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.create_scheduled_event(guild_id, **kwargs)

    async def update_scheduled_event(self, guild_id: str, event_id: str, **kwargs) -> dict:
        return await self._rest_client.update_scheduled_event(guild_id, event_id, **kwargs)

    async def delete_scheduled_event(self, guild_id: str, event_id: str) -> None:
        await self._rest_client.delete_scheduled_event(guild_id, event_id)

    async def list_scheduled_event_users(
        self, guild_id: str, event_id: str, **kwargs
    ) -> list[dict]:
        return await self._rest_client.list_scheduled_event_users(guild_id, event_id, **kwargs)

    # --- Emojis ---

    async def list_emojis(self, guild_id: str) -> list[dict]:
        return await self._rest_client.list_guild_emojis(guild_id)

    async def get_emoji(self, guild_id: str, emoji_id: str) -> dict:
        return await self._rest_client.get_guild_emoji(guild_id, emoji_id)

    async def create_emoji(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.create_guild_emoji(guild_id, **kwargs)

    async def update_emoji(self, guild_id: str, emoji_id: str, **kwargs) -> dict:
        return await self._rest_client.update_guild_emoji(guild_id, emoji_id, **kwargs)

    async def delete_emoji(self, guild_id: str, emoji_id: str) -> None:
        await self._rest_client.delete_guild_emoji(guild_id, emoji_id)

    # --- Stickers ---

    async def list_stickers(self, guild_id: str) -> list[dict]:
        return await self._rest_client.list_guild_stickers(guild_id)

    async def create_sticker(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.create_guild_sticker(guild_id, **kwargs)

    async def delete_sticker(self, guild_id: str, sticker_id: str) -> None:
        await self._rest_client.delete_guild_sticker(guild_id, sticker_id)

    # --- Voice States ---

    async def update_self_voice_state(self, guild_id: str, **kwargs) -> None:
        await self._rest_client.update_self_voice_state(guild_id, **kwargs)

    async def update_member_voice_state(self, guild_id: str, user_id: str, **kwargs) -> None:
        await self._rest_client.update_voice_state(guild_id, user_id, **kwargs)

    # --- Voice Regions ---

    async def list_voice_regions(self) -> list[dict]:
        return await self._rest_client.list_voice_regions()

    # --- Vanity URL ---

    async def get_vanity_url(self, guild_id: str) -> dict:
        return await self._rest_client.get_vanity_url(guild_id)

    # --- DM Channels ---

    async def create_dm(self, recipient_id: str) -> dict:
        return await self._rest_client.create_dm(recipient_id)

    # --- Guild Widget ---

    async def get_guild_widget(self, guild_id: str) -> dict:
        return await self._rest_client.get_guild_widget(guild_id)

    async def update_guild_widget(self, guild_id: str, **kwargs) -> dict:
        return await self._rest_client.update_guild_widget(guild_id, **kwargs)

    # --- Leave Guild ---

    async def leave_guild(self, guild_id: str) -> None:
        await self._rest_client.leave_guild(guild_id)

    # --- New Member Welcome ---

    async def get_new_member_welcome(self, guild_id: str) -> dict:
        return await self._rest_client.get_new_member_welcome(guild_id)

    # --- Invite Target Users ---

    async def get_invite_target_users(self, code: str) -> dict:
        return await self._rest_client.get_invite_target_users(code)

    async def update_invite_target_users(self, code: str, **kwargs) -> dict:
        return await self._rest_client.update_invite_target_users(code, **kwargs)

    # --- Bot ---

    async def get_bot_info(self) -> dict:
        return await self._rest_client.get_current_user()

    # --- Slash Commands ---

    async def register_guild_command(
        self,
        application_id: str,
        guild_id: str,
        name: str,
        description: str,
        options: list[dict] | None = None,
    ) -> dict:
        kwargs = {}
        if options:
            kwargs["options"] = options
        return await self._rest_client.create_guild_application_command(
            application_id, guild_id, name, description, **kwargs
        )

    async def respond_to_interaction(
        self, interaction_id: str, interaction_token: str, content: str, ephemeral: bool = False
    ) -> None:
        data: dict = {"content": content}
        if ephemeral:
            data["flags"] = 64
        await self._rest_client.create_interaction_response(
            interaction_id, interaction_token, response_type=4, data=data
        )

    # --- Lifecycle ---

    async def start(self) -> None:
        info = await self.get_bot_info()
        self._bot_id: str | None = info.get("id")

    async def close(self) -> None:
        await self._rest_client.close()
