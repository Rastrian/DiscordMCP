# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from typing import TYPE_CHECKING

from discord_mcp_platform.automations.definitions import ActionType

if TYPE_CHECKING:
    from discord_mcp_platform.discord.bot_runtime import BotRuntime


class ActionExecutor:
    def __init__(self, bot: BotRuntime | None = None) -> None:
        self._bot = bot

    async def execute(self, action_type: ActionType, action_config: dict, context: dict) -> dict:
        if action_type == ActionType.SEND_MESSAGE:
            return await self._send_message(action_config, context)
        elif action_type == ActionType.DELETE_MESSAGE:
            return await self._delete_message(action_config, context)
        elif action_type == ActionType.ADD_ROLE:
            return await self._add_role(action_config, context)
        elif action_type == ActionType.REMOVE_ROLE:
            return await self._remove_role(action_config, context)
        elif action_type == ActionType.CREATE_THREAD:
            return await self._create_thread(action_config, context)
        return {"status": "unknown_action"}

    async def _send_message(self, config: dict, ctx: dict) -> dict:
        if not self._bot:
            return {"status": "error", "error": "no_bot"}
        channel_id = config.get("channel_id") or ctx.get("channel_id")
        content = config.get("content", "")
        if not channel_id or not content:
            return {"status": "error", "error": "missing_channel_or_content"}
        msg = await self._bot.send_message(str(channel_id), content)
        return {"status": "sent", "message_id": msg.id}

    async def _delete_message(self, config: dict, ctx: dict) -> dict:
        if not self._bot:
            return {"status": "error", "error": "no_bot"}
        channel_id = config.get("channel_id") or ctx.get("channel_id")
        message_id = config.get("message_id") or ctx.get("message_id")
        if not channel_id or not message_id:
            return {"status": "error", "error": "missing_ids"}
        await self._bot.delete_message(str(channel_id), str(message_id))
        return {"status": "deleted"}

    async def _add_role(self, config: dict, ctx: dict) -> dict:
        if not self._bot:
            return {"status": "error", "error": "no_bot"}
        guild_id = config.get("guild_id") or ctx.get("guild_id")
        user_id = config.get("user_id") or ctx.get("user_id")
        role_id = config.get("role_id")
        if not all([guild_id, user_id, role_id]):
            return {"status": "error", "error": "missing_ids"}
        await self._bot.add_role(str(guild_id), str(user_id), str(role_id))
        return {"status": "role_added"}

    async def _remove_role(self, config: dict, ctx: dict) -> dict:
        if not self._bot:
            return {"status": "error", "error": "no_bot"}
        guild_id = config.get("guild_id") or ctx.get("guild_id")
        user_id = config.get("user_id") or ctx.get("user_id")
        role_id = config.get("role_id")
        if not all([guild_id, user_id, role_id]):
            return {"status": "error", "error": "missing_ids"}
        await self._bot.remove_role(str(guild_id), str(user_id), str(role_id))
        return {"status": "role_removed"}

    async def _create_thread(self, config: dict, ctx: dict) -> dict:
        if not self._bot:
            return {"status": "error", "error": "no_bot"}
        channel_id = config.get("channel_id") or ctx.get("channel_id")
        name = config.get("name", "New Thread")
        message_id = config.get("message_id") or ctx.get("message_id")
        if not channel_id:
            return {"status": "error", "error": "missing_channel"}
        thread = await self._bot.create_thread(
            str(channel_id),
            name,
            message_id=str(message_id) if message_id else None,
        )
        return {"status": "created", "thread_id": thread.id}
