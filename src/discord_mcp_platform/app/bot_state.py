# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.discord.bot_runtime import BotRuntime

_bot: BotRuntime | None = None


def get_bot() -> BotRuntime | None:
    return _bot


def set_bot(bot: BotRuntime | None) -> None:
    global _bot
    _bot = bot
