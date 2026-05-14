# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

import asyncio

import httpx

from discord_mcp_platform.discord.rate_limits import RateLimitTracker
from discord_mcp_platform.errors import DiscordNotFoundError, ExternalServiceError, RateLimitError

DISCORD_API_BASE = "https://discord.com/api/v10"


class DiscordRestClient:
    def __init__(self, bot_token: str) -> None:
        self._client = httpx.AsyncClient(
            base_url=DISCORD_API_BASE,
            headers={"Authorization": f"Bot {bot_token}"},
        )
        self._rate_limiter = RateLimitTracker()

    # --- Guilds ---

    async def get_guilds(self) -> list[dict]:
        return await self._request("GET", "/users/@me/guilds")

    async def get_guild(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}")

    # --- Channels ---

    async def get_channels(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/channels")

    async def get_channel(self, channel_id: str) -> dict:
        return await self._request("GET", f"/channels/{channel_id}")

    async def create_channel(
        self, guild_id: str, name: str, channel_type: int = 0, **kwargs
    ) -> dict:
        body: dict = {"name": name, "type": channel_type, **kwargs}
        return await self._request("POST", f"/guilds/{guild_id}/channels", json=body)

    async def modify_channel(self, channel_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/channels/{channel_id}", json=kwargs)

    async def delete_channel(self, channel_id: str) -> dict:
        return await self._request("DELETE", f"/channels/{channel_id}")

    # --- Messages ---

    async def get_messages(self, channel_id: str, limit: int = 50) -> list[dict]:
        return await self._request(
            "GET", f"/channels/{channel_id}/messages", params={"limit": limit}
        )

    async def send_message(self, channel_id: str, content: str) -> dict:
        return await self._request(
            "POST", f"/channels/{channel_id}/messages", json={"content": content}
        )

    async def send_rich_message(
        self, channel_id: str, content: str | None = None, embeds: list[dict] | None = None
    ) -> dict:
        body: dict = {}
        if content:
            body["content"] = content
        if embeds:
            body["embeds"] = embeds
        return await self._request("POST", f"/channels/{channel_id}/messages", json=body)

    async def edit_message(
        self,
        channel_id: str,
        message_id: str,
        content: str | None = None,
        embeds: list[dict] | None = None,
    ) -> dict:
        body: dict = {}
        if content is not None:
            body["content"] = content
        if embeds is not None:
            body["embeds"] = embeds
        return await self._request(
            "PATCH", f"/channels/{channel_id}/messages/{message_id}", json=body
        )

    async def delete_message(self, channel_id: str, message_id: str) -> None:
        await self._request("DELETE", f"/channels/{channel_id}/messages/{message_id}")

    async def bulk_delete_messages(self, channel_id: str, message_ids: list[str]) -> None:
        await self._request(
            "POST", f"/channels/{channel_id}/messages/bulk-delete", json={"messages": message_ids}
        )

    # --- Threads ---

    async def create_thread(
        self, channel_id: str, name: str, message_id: str | None = None, private: bool = False
    ) -> dict:
        body: dict = {"name": name}
        if message_id is not None:
            body["type"] = 11
            return await self._request(
                "POST", f"/channels/{channel_id}/messages/{message_id}/threads", json=body
            )
        body["type"] = 12 if private else 11
        return await self._request("POST", f"/channels/{channel_id}/threads", json=body)

    # --- Members ---

    async def get_guild_member(self, guild_id: str, user_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/members/{user_id}")

    async def list_guild_members(
        self, guild_id: str, limit: int = 100, after: str = "0"
    ) -> list[dict]:
        return await self._request(
            "GET", f"/guilds/{guild_id}/members", params={"limit": limit, "after": after}
        )

    async def modify_guild_member(self, guild_id: str, user_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/guilds/{guild_id}/members/{user_id}", json=kwargs)

    async def kick_member(self, guild_id: str, user_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/members/{user_id}")

    async def ban_member(
        self, guild_id: str, user_id: str, delete_message_days: int = 0, reason: str = ""
    ) -> None:
        body: dict = {"delete_message_days": delete_message_days}
        if reason:
            body["reason"] = reason
        await self._request("PUT", f"/guilds/{guild_id}/bans/{user_id}", json=body)

    async def unban_member(self, guild_id: str, user_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/bans/{user_id}")

    # --- Roles ---

    async def list_guild_roles(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/roles")

    async def add_guild_member_role(self, guild_id: str, user_id: str, role_id: str) -> None:
        await self._request("PUT", f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}")

    async def remove_guild_member_role(self, guild_id: str, user_id: str, role_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/members/{user_id}/roles/{role_id}")

    async def create_guild_role(self, guild_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/guilds/{guild_id}/roles", json=kwargs)

    async def modify_guild_role(self, guild_id: str, role_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/guilds/{guild_id}/roles/{role_id}", json=kwargs)

    async def modify_guild_role_positions(self, guild_id: str, positions: list[dict]) -> list[dict]:
        return await self._request("PATCH", f"/guilds/{guild_id}/roles", json=positions)

    async def delete_guild_role(self, guild_id: str, role_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/roles/{role_id}")

    # --- Guild (new) ---

    async def modify_guild(self, guild_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/guilds/{guild_id}", json=kwargs)

    # --- Webhooks ---

    async def create_webhook(self, channel_id: str, name: str, avatar: str | None = None) -> dict:
        body: dict = {"name": name}
        if avatar:
            body["avatar"] = avatar
        return await self._request("POST", f"/channels/{channel_id}/webhooks", json=body)

    async def list_channel_webhooks(self, channel_id: str) -> list[dict]:
        return await self._request("GET", f"/channels/{channel_id}/webhooks")

    async def list_guild_webhooks(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/webhooks")

    async def get_webhook(self, webhook_id: str) -> dict:
        return await self._request("GET", f"/webhooks/{webhook_id}")

    async def modify_webhook(self, webhook_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/webhooks/{webhook_id}", json=kwargs)

    async def delete_webhook(self, webhook_id: str) -> None:
        await self._request("DELETE", f"/webhooks/{webhook_id}")

    async def execute_webhook(self, webhook_id: str, webhook_token: str, **kwargs) -> dict:
        return await self._request(
            "POST",
            f"/webhooks/{webhook_id}/{webhook_token}",
            json=kwargs,
            params={"wait": "true"},
        )

    async def edit_webhook_message(
        self, webhook_id: str, token: str, message_id: str, **kwargs
    ) -> dict:
        return await self._request(
            "PATCH",
            f"/webhooks/{webhook_id}/{token}/messages/{message_id}",
            json=kwargs,
        )

    async def delete_webhook_message(self, webhook_id: str, token: str, message_id: str) -> None:
        await self._request("DELETE", f"/webhooks/{webhook_id}/{token}/messages/{message_id}")

    # --- Channel Permissions ---

    async def edit_channel_permissions(
        self, channel_id: str, overwrite_id: str, allow: str, deny: str, overwrite_type: int
    ) -> None:
        await self._request(
            "PUT",
            f"/channels/{channel_id}/permissions/{overwrite_id}",
            json={"allow": allow, "deny": deny, "type": overwrite_type},
        )

    async def delete_channel_permissions(self, channel_id: str, overwrite_id: str) -> None:
        await self._request("DELETE", f"/channels/{channel_id}/permissions/{overwrite_id}")

    # --- Invites ---

    async def get_channel_invites(self, channel_id: str) -> list[dict]:
        return await self._request("GET", f"/channels/{channel_id}/invites")

    async def get_guild_invites(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/invites")

    async def create_channel_invite(self, channel_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/channels/{channel_id}/invites", json=kwargs)

    async def get_invite(self, code: str) -> dict:
        return await self._request("GET", f"/invites/{code}")

    async def delete_invite(self, code: str) -> None:
        await self._request("DELETE", f"/invites/{code}")

    # --- Pins ---

    async def get_pinned_messages(self, channel_id: str) -> list[dict]:
        return await self._request("GET", f"/channels/{channel_id}/pins")

    async def pin_message(self, channel_id: str, message_id: str) -> None:
        await self._request("PUT", f"/channels/{channel_id}/pins/{message_id}")

    async def unpin_message(self, channel_id: str, message_id: str) -> None:
        await self._request("DELETE", f"/channels/{channel_id}/pins/{message_id}")

    # --- Reactions ---

    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        await self._request(
            "PUT", f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        )

    async def delete_own_reaction(self, channel_id: str, message_id: str, emoji: str) -> None:
        await self._request(
            "DELETE", f"/channels/{channel_id}/messages/{message_id}/reactions/{emoji}/@me"
        )

    # --- Crosspost ---

    async def crosspost_message(self, channel_id: str, message_id: str) -> dict:
        return await self._request(
            "POST", f"/channels/{channel_id}/messages/{message_id}/crosspost"
        )

    # --- Typing ---

    async def trigger_typing(self, channel_id: str) -> None:
        await self._request("POST", f"/channels/{channel_id}/typing")

    # --- Active Threads ---

    async def list_active_threads(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/threads/active")

    # --- Archived Threads ---

    async def list_public_archived_threads(self, channel_id: str, **kwargs) -> dict:
        return await self._request(
            "GET", f"/channels/{channel_id}/threads/archived/public", params=kwargs
        )

    async def list_private_archived_threads(self, channel_id: str, **kwargs) -> dict:
        return await self._request(
            "GET", f"/channels/{channel_id}/threads/archived/private", params=kwargs
        )

    async def list_joined_private_archived_threads(self, channel_id: str, **kwargs) -> dict:
        return await self._request(
            "GET", f"/channels/{channel_id}/users/@me/threads/archived/private", params=kwargs
        )

    # --- Thread Members ---

    async def list_thread_members(self, channel_id: str) -> list[dict]:
        return await self._request("GET", f"/channels/{channel_id}/thread-members")

    # --- Audit Logs ---

    async def get_audit_log(self, guild_id: str, **kwargs) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/audit-logs", params=kwargs)

    # --- Member Search ---

    async def search_guild_members(self, guild_id: str, query: str, **kwargs) -> list[dict]:
        params = {"query": query, **kwargs}
        return await self._request("GET", f"/guilds/{guild_id}/members/search", params=params)

    # --- Bulk Ban ---

    async def bulk_ban_members(self, guild_id: str, user_ids: list[str], **kwargs) -> dict:
        body = {"user_ids": user_ids, **kwargs}
        return await self._request("POST", f"/guilds/{guild_id}/bulk-ban", json=body)

    # --- Prune ---

    async def get_prune_count(self, guild_id: str, **kwargs) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/prune", params=kwargs)

    async def begin_prune(self, guild_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/guilds/{guild_id}/prune", json=kwargs)

    # --- Guild Preview ---

    async def get_guild_preview(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/preview")

    # --- Onboarding ---

    async def get_guild_onboarding(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/onboarding")

    async def update_guild_onboarding(self, guild_id: str, **kwargs) -> dict:
        return await self._request("PUT", f"/guilds/{guild_id}/onboarding", json=kwargs)

    # --- Welcome Screen ---

    async def get_guild_welcome_screen(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/welcome-screen")

    async def update_guild_welcome_screen(self, guild_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/guilds/{guild_id}/welcome-screen", json=kwargs)

    # --- Auto-Moderation ---

    async def list_auto_moderation_rules(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/auto-moderation/rules")

    async def get_auto_moderation_rule(self, guild_id: str, rule_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/auto-moderation/rules/{rule_id}")

    async def create_auto_moderation_rule(self, guild_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/guilds/{guild_id}/auto-moderation/rules", json=kwargs)

    async def update_auto_moderation_rule(self, guild_id: str, rule_id: str, **kwargs) -> dict:
        return await self._request(
            "PATCH", f"/guilds/{guild_id}/auto-moderation/rules/{rule_id}", json=kwargs
        )

    async def delete_auto_moderation_rule(self, guild_id: str, rule_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/auto-moderation/rules/{rule_id}")

    # --- Scheduled Events ---

    async def list_scheduled_events(self, guild_id: str, **kwargs) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/scheduled-events", params=kwargs)

    async def get_scheduled_event(self, guild_id: str, event_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/scheduled-events/{event_id}")

    async def create_scheduled_event(self, guild_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/guilds/{guild_id}/scheduled-events", json=kwargs)

    async def update_scheduled_event(self, guild_id: str, event_id: str, **kwargs) -> dict:
        return await self._request(
            "PATCH", f"/guilds/{guild_id}/scheduled-events/{event_id}", json=kwargs
        )

    async def delete_scheduled_event(self, guild_id: str, event_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/scheduled-events/{event_id}")

    async def list_scheduled_event_users(
        self, guild_id: str, event_id: str, **kwargs
    ) -> list[dict]:
        return await self._request(
            "GET", f"/guilds/{guild_id}/scheduled-events/{event_id}/users", params=kwargs
        )

    # --- Emojis ---

    async def list_guild_emojis(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/emojis")

    async def get_guild_emoji(self, guild_id: str, emoji_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/emojis/{emoji_id}")

    async def create_guild_emoji(self, guild_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/guilds/{guild_id}/emojis", json=kwargs)

    async def update_guild_emoji(self, guild_id: str, emoji_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/guilds/{guild_id}/emojis/{emoji_id}", json=kwargs)

    async def delete_guild_emoji(self, guild_id: str, emoji_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/emojis/{emoji_id}")

    # --- Stickers ---

    async def list_guild_stickers(self, guild_id: str) -> list[dict]:
        return await self._request("GET", f"/guilds/{guild_id}/stickers")

    async def get_guild_sticker(self, guild_id: str, sticker_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/stickers/{sticker_id}")

    async def create_guild_sticker(self, guild_id: str, **kwargs) -> dict:
        return await self._request("POST", f"/guilds/{guild_id}/stickers", json=kwargs)

    async def update_guild_sticker(self, guild_id: str, sticker_id: str, **kwargs) -> dict:
        return await self._request(
            "PATCH", f"/guilds/{guild_id}/stickers/{sticker_id}", json=kwargs
        )

    async def delete_guild_sticker(self, guild_id: str, sticker_id: str) -> None:
        await self._request("DELETE", f"/guilds/{guild_id}/stickers/{sticker_id}")

    # --- Voice States ---

    async def update_self_voice_state(self, guild_id: str, **kwargs) -> None:
        await self._request("PATCH", f"/guilds/{guild_id}/voice-states/@me", json=kwargs)

    async def update_voice_state(self, guild_id: str, user_id: str, **kwargs) -> None:
        await self._request("PATCH", f"/guilds/{guild_id}/voice-states/{user_id}", json=kwargs)

    # --- Voice Regions ---

    async def list_voice_regions(self) -> list[dict]:
        return await self._request("GET", "/voice/regions")

    # --- Vanity URL ---

    async def get_vanity_url(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/vanity-url")

    # --- DM Channels ---

    async def create_dm(self, recipient_id: str) -> dict:
        return await self._request(
            "POST", "/users/@me/channels", json={"recipient_id": recipient_id}
        )

    # --- Guild Widget ---

    async def get_guild_widget(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/widget")

    async def update_guild_widget(self, guild_id: str, **kwargs) -> dict:
        return await self._request("PATCH", f"/guilds/{guild_id}/widget", json=kwargs)

    # --- Leave Guild ---

    async def leave_guild(self, guild_id: str) -> None:
        await self._request("DELETE", f"/users/@me/guilds/{guild_id}")

    # --- New Member Welcome ---

    async def get_new_member_welcome(self, guild_id: str) -> dict:
        return await self._request("GET", f"/guilds/{guild_id}/new-member-welcome")

    # --- Invite Target Users ---

    async def get_invite_target_users(self, code: str) -> dict:
        return await self._request("GET", f"/invites/{code}/target-users")

    async def update_invite_target_users(self, code: str, **kwargs) -> dict:
        return await self._request("PUT", f"/invites/{code}/target-users", json=kwargs)

    # --- Bot ---

    async def get_current_user(self) -> dict:
        return await self._request("GET", "/users/@me")

    # --- Application Commands ---

    async def create_guild_application_command(
        self, application_id: str, guild_id: str, name: str, description: str, **kwargs
    ) -> dict:
        body: dict = {"name": name, "description": description, **kwargs}
        return await self._request(
            "POST", f"/applications/{application_id}/guilds/{guild_id}/commands", json=body
        )

    async def bulk_set_guild_application_commands(
        self, application_id: str, guild_id: str, commands: list[dict]
    ) -> list[dict]:
        return await self._request(
            "PUT", f"/applications/{application_id}/guilds/{guild_id}/commands", json=commands
        )

    # --- Interactions ---

    async def create_interaction_response(
        self,
        interaction_id: str,
        interaction_token: str,
        response_type: int,
        data: dict | None = None,
    ) -> None:
        body: dict = {"type": response_type}
        if data is not None:
            body["data"] = data
        await self._request(
            "POST", f"/interactions/{interaction_id}/{interaction_token}/callback", json=body
        )

    # --- Lifecycle ---

    async def close(self) -> None:
        await self._client.aclose()

    # --- Internal ---

    async def _request(self, method: str, path: str, **kwargs) -> list[dict] | dict | None:
        bucket = f"{method}:{path}"
        if self._rate_limiter.is_limited(bucket):
            wait = self._rate_limiter.wait_time(bucket)
            if wait > 0:
                await asyncio.sleep(wait)

        response = await self._client.request(method, path, **kwargs)
        self._update_rate_limits(bucket, response)
        self._handle_response(response)

        if response.status_code == 204:
            return None
        return response.json()

    def _update_rate_limits(self, bucket: str, response: httpx.Response) -> None:
        remaining = response.headers.get("x-ratelimit-remaining")
        reset_after = response.headers.get("x-ratelimit-reset-after")
        if remaining is not None and reset_after is not None:
            import time

            self._rate_limiter.update(
                bucket,
                remaining=int(remaining),
                reset_at=time.monotonic() + float(reset_after),
            )

    def _handle_response(self, response: httpx.Response) -> None:
        if response.status_code == 429:
            data = response.json()
            retry_after = data.get("retry_after")
            raise RateLimitError(
                retry_after=float(retry_after) if retry_after is not None else None
            )
        if response.status_code == 404:
            raise DiscordNotFoundError(response.text)
        if response.status_code == 204:
            return
        if response.status_code >= 400:
            raise ExternalServiceError(f"Discord API error {response.status_code}: {response.text}")
