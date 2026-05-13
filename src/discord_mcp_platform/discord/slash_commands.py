# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from typing import TYPE_CHECKING, Callable, Awaitable

from discord_mcp_platform.app.logging import get_logger

if TYPE_CHECKING:
    from discord_mcp_platform.discord.bot_runtime import BotRuntime

log = get_logger("slash_commands")

ADMINISTRATOR = 0x8

COMMAND_DEFINITIONS = [
    {
        "name": "allow-chat",
        "description": "Allow the bot to chat in a channel",
        "options": [
            {
                "name": "channel",
                "description": "The channel to allow",
                "type": 7,
                "required": True,
            }
        ],
    },
    {
        "name": "disallow-chat",
        "description": "Remove the bot's chat access from a channel",
        "options": [
            {
                "name": "channel",
                "description": "The channel to disallow",
                "type": 7,
                "required": True,
            }
        ],
    },
]


class SlashCommandHandler:
    def __init__(self, bot: BotRuntime, session_factory: Callable[[], Awaitable]) -> None:
        self._bot = bot
        self._session_factory = session_factory

    async def register_commands(self, guild_ids: list[str]) -> None:
        application_id = self._bot.bot_id
        if not application_id:
            log.warning("slash_commands_no_bot_id")
            return

        for guild_id in guild_ids:
            try:
                await self._bot._rest_client.bulk_set_guild_application_commands(
                    application_id, guild_id, COMMAND_DEFINITIONS
                )
                log.info("slash_commands_registered", guild_id=guild_id)
            except Exception as e:
                log.warning("slash_commands_register_failed", guild_id=guild_id, error=str(e))

    async def handle_interaction(self, event: dict) -> bool:
        if event.get("type") != 2:
            return False

        data = event.get("data", {})
        command_name = data.get("name", "")
        if command_name not in ("allow-chat", "disallow-chat"):
            return False

        guild_id = event.get("guild_id", "")
        member = event.get("member", {})
        user_id = member.get("user", {}).get("id", "")
        interaction_id = event.get("id", "")
        interaction_token = event.get("token", "")

        # Permission check: owner or admin
        if not await self._is_admin_or_owner(guild_id, member, user_id):
            await self._bot.respond_to_interaction(
                interaction_id,
                interaction_token,
                "Only server owners and administrators can use this command.",
                ephemeral=True,
            )
            return True

        options = {opt["name"]: opt["value"] for opt in data.get("options", [])}
        target_channel_id = str(options.get("channel", ""))

        if command_name == "allow-chat":
            await self._allow_channel(
                guild_id, target_channel_id, user_id, interaction_id, interaction_token
            )
        elif command_name == "disallow-chat":
            await self._disallow_channel(
                guild_id, target_channel_id, interaction_id, interaction_token
            )

        return True

    async def _is_admin_or_owner(self, guild_id: str, member: dict, user_id: str) -> bool:
        try:
            guild_data = await self._bot.rest.get_guild(guild_id)
            if guild_data.get("owner_id") == user_id:
                return True
        except Exception:
            pass
        permissions = int(member.get("permissions", "0"))
        return (permissions & ADMINISTRATOR) == ADMINISTRATOR

    async def _allow_channel(
        self,
        guild_id: str,
        channel_id: str,
        user_id: str,
        interaction_id: str,
        interaction_token: str,
    ) -> None:
        from sqlalchemy import select
        from discord_mcp_platform.db.models import AllowedChatChannel

        async with self._session_factory() as session:
            existing = (
                await session.execute(
                    select(AllowedChatChannel).where(
                        AllowedChatChannel.guild_id == guild_id,
                        AllowedChatChannel.channel_id == channel_id,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                await self._bot.respond_to_interaction(
                    interaction_id,
                    interaction_token,
                    "That channel is already allowed.",
                    ephemeral=True,
                )
                return

            try:
                ch = await self._bot.get_channel(channel_id)
                ch_name = ch.name
            except Exception:
                ch_name = None

            record = AllowedChatChannel(
                guild_id=guild_id,
                channel_id=channel_id,
                channel_name=ch_name,
                allowed_by_user_id=user_id,
            )
            session.add(record)
            await session.commit()

        await self._bot.respond_to_interaction(
            interaction_id,
            interaction_token,
            f"Chat enabled in <#{channel_id}>.",
            ephemeral=True,
        )

    async def _disallow_channel(
        self, guild_id: str, channel_id: str, interaction_id: str, interaction_token: str
    ) -> None:
        from sqlalchemy import select
        from discord_mcp_platform.db.models import AllowedChatChannel

        async with self._session_factory() as session:
            existing = (
                await session.execute(
                    select(AllowedChatChannel).where(
                        AllowedChatChannel.guild_id == guild_id,
                        AllowedChatChannel.channel_id == channel_id,
                    )
                )
            ).scalar_one_or_none()

            if not existing:
                await self._bot.respond_to_interaction(
                    interaction_id,
                    interaction_token,
                    "That channel is not in the allowed list.",
                    ephemeral=True,
                )
                return

            await session.delete(existing)
            await session.commit()

        await self._bot.respond_to_interaction(
            interaction_id,
            interaction_token,
            f"Chat disabled in <#{channel_id}>.",
            ephemeral=True,
        )
