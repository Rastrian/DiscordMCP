# Copyright 2026 Luis Gustavo Vaz <me@rastrian.dev>
#
# Licensed under the Apache License, Version 2.0.
# See the LICENSE file in the project root for details.

from __future__ import annotations

from discord_mcp_platform.errors import AuthorizationError, PolicyDeniedError

DANGEROUS_OPERATIONS: frozenset[str] = frozenset(
    {
        "message.send",
        "message.delete",
        "message.bulk_delete",
        "message.edit",
        "channel.permission_change",
        "channel.create",
        "channel.edit",
        "role.assign",
        "role.remove",
        "role.create",
        "role.modify",
        "role.delete",
        "member.timeout",
        "member.ban",
        "member.kick",
        "member.unban",
        "channel.delete",
        "webhook.create",
        "webhook.delete",
        "webhook.modify",
        "webhook.execute",
        "guild.modify",
        "invite.create",
        "invite.delete",
        "automation.change",
        "thread.create",
    }
)


def _parse_scopes(scopes: str) -> set[str]:
    return {s.strip() for s in scopes.split(",") if s.strip()}


class PermissionService:
    def __init__(self, allowed_guild_ids: list[str], allowed_channel_ids: list[str]) -> None:
        self._allowed_guild_ids = allowed_guild_ids
        self._allowed_channel_ids = allowed_channel_ids

    def check_guild_allowed(self, guild_id: str) -> bool:
        if not self._allowed_guild_ids:
            return True
        return guild_id in self._allowed_guild_ids

    def check_channel_allowed(self, channel_id: str) -> bool:
        if not self._allowed_channel_ids:
            return True
        return channel_id in self._allowed_channel_ids

    def check_read(self, scopes: str, resource: str) -> None:
        if f"{resource}:read" not in _parse_scopes(scopes):
            raise AuthorizationError(f"missing {resource}:read scope")

    def check_write(self, scopes: str, resource: str) -> None:
        if f"{resource}:write" not in _parse_scopes(scopes):
            raise AuthorizationError(f"missing {resource}:write scope")

    def check_dangerous_operation(
        self,
        operation: str,
        dry_run: bool,
        confirmation: str | None,
    ) -> None:
        if operation not in DANGEROUS_OPERATIONS:
            return
        if dry_run:
            return
        if confirmation is None:
            raise PolicyDeniedError(
                f"operation {operation!r} requires dry_run=True or explicit confirmation"
            )

    def validate_scopes(self, required: str, provided: str) -> bool:
        provided_set = _parse_scopes(provided)
        return required.strip() in provided_set
