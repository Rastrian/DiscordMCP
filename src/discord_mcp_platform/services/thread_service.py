# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.app.logging import get_logger
from discord_mcp_platform.discord.models import ThreadCreateInput, ThreadCreateOutput
from discord_mcp_platform.discord.bot_runtime import BotRuntime
from discord_mcp_platform.security.policy import PermissionService

log = get_logger("thread_service")


class ThreadService:
    def __init__(self, bot: BotRuntime, permissions: PermissionService) -> None:
        self._bot = bot
        self._permissions = permissions

    async def create(self, input_data: ThreadCreateInput, scopes: str) -> ThreadCreateOutput:
        self._permissions.check_write(scopes, "thread")
        self._permissions.check_dangerous_operation(
            "thread.create", input_data.dry_run, input_data.confirmation
        )
        if not self._permissions.check_channel_allowed(input_data.channel_id):
            from discord_mcp_platform.errors import PolicyDeniedError

            raise PolicyDeniedError(f"channel {input_data.channel_id} is not allowed")

        if input_data.dry_run:
            log.info(
                "thread_create_dry_run", channel_id=input_data.channel_id, name=input_data.name
            )
            return ThreadCreateOutput(status="validated", dry_run=True, thread_id=None)

        thread = await self._bot.create_thread(
            input_data.channel_id,
            input_data.name,
            input_data.message_id,
            input_data.private,
        )
        log.info("thread_created", thread_id=thread.id, channel_id=input_data.channel_id)
        return ThreadCreateOutput(status="created", dry_run=False, thread_id=thread.id)
