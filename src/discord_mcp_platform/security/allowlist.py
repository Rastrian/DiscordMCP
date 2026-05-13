# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations


class Allowlist:
    def __init__(self, guild_ids: list[str], channel_ids: list[str]) -> None:
        self._guild_ids = set(guild_ids)
        self._channel_ids = set(channel_ids)

    def is_guild_allowed(self, guild_id: str) -> bool:
        if not self._guild_ids:
            return True
        return guild_id in self._guild_ids

    def is_channel_allowed(self, channel_id: str) -> bool:
        if not self._channel_ids:
            return True
        return channel_id in self._channel_ids

    def filter_guilds(self, guild_ids: list[str]) -> list[str]:
        if not self._guild_ids:
            return list(guild_ids)
        return [gid for gid in guild_ids if gid in self._guild_ids]

    def filter_channels(self, channel_ids: list[str]) -> list[str]:
        if not self._channel_ids:
            return list(channel_ids)
        return [cid for cid in channel_ids if cid in self._channel_ids]
